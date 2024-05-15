from fastapi import FastAPI, Depends, HTTPException, Request

from app.database.base import get_db, engine
from app.database import models

from sqlalchemy.orm import Session
from fastapi import FastAPI, File, UploadFile

from app.nodes.pychunk_nodes_creation import create_nodes
from app.nodes.node_postprocessor import NodePostProccesor
from app.embeddings import HugginFaceEmbeddings

import os, shutil, httpx, json
from zipfile import ZipFile

models.Base.metadata.create_all(bind=engine)
app = FastAPI()
embeddings = HugginFaceEmbeddings()

@app.get("/")
async def main_page():
  return {'msg': 'welcome to the main page!'}

@app.post("/create_nodes_store")
async def upload_file_zip(file: UploadFile = File(...), db: Session = Depends(get_db)):

    extract_dir = os.environ['USER_CODE_DIRECTORY']
    if not os.path.exists(extract_dir):
        
        os.makedirs(extract_dir, exist_ok=True)

        with open(f"{extract_dir}/{file.filename}", "wb") as buffer:
            buffer.write(await file.read())

        with ZipFile(f"{extract_dir}/{file.filename}", "r") as zip_ref:
            zip_ref.extractall(extract_dir)
            
        os.remove(f"{extract_dir}/{file.filename}")
        if os.path.exists(f"{extract_dir}/__MACOSX"):
            shutil.rmtree(f"{extract_dir}/__MACOSX")
        if os.path.exists(f"{extract_dir}/.venv"):
            shutil.rmtree(f"{extract_dir}/.venv")
        if os.path.exists(f"{extract_dir}/.ipynb_checkpoints"):
            shutil.rmtree(f"{extract_dir}/.ipynb_checkpoints")
    
    else:
        shutil.rmtree(extract_dir)

    py_files = create_nodes(path=extract_dir, db=db)
    return {"py_files": py_files}

@app.get("/get_text_from_node/{node_id}", response_model=None)
async def get_text_from_node(node_id: str, db: Session = Depends(get_db)):
    node = db.query(models.Node).filter(models.Node.id == node_id).first()
    if node is None:
        raise HTTPException(status_code=404, detail=f"Node: {node_id} does not exist")
    text_data = db.query(models.Node.text).filter(models.Node.parent_node_id == node_id).all()
    texts = [text[0] for text in text_data]

    return {"code": "".join(texts)}

@app.get("/query_vector_database")
async def query_vector_database(request: Request, db: Session = Depends(get_db)):
    
    from .nodes.node_retriever import NodeRetriever
    import numpy as np
    
    body = await request.json()
    code = body['code']
    
    node_retriever = NodeRetriever(query=code, db=db)
    
    # we retrieve the nodes based on the query performing similiarity search 
    _, nodes_with_score = node_retriever._retrieve_nodes()
        
    # we compute the mean of the similarity scores to eliminate those nodes with score below the minimum
    score_mean = np.mean([n.score for n in nodes_with_score])
    node_post_proccesor = NodePostProccesor(retrieved_nodes_score=nodes_with_score, db=db, score_threshold=score_mean)
    
    # we get the most frequent parent_node and file_node of the retrieved nodes
    parent_node_freq, file_node_freq = node_post_proccesor._check_common_parent_nodes()
    
    # we get the nodes with higher score than the mean score
    nodes_with_score = node_post_proccesor.return_nodes_with_score_after_apply_threshold_filter()
    
    # we do not want the nodes with a score that is too small in comparison with the highest one
    maximum_score = max(nodes_with_score, key=lambda x: x.score).score
    relative_diffs = [(maximum_score - n.score) / (maximum_score + n.score) for n in nodes_with_score]

    not_valid_nodes_with_score = []
    for index, relative_diff in enumerate(relative_diffs):
        if relative_diff >= float(os.environ['RELATIVE_DIFF']):
            not_valid_nodes_with_score.append(nodes_with_score[index])
    
    # also, we do not want to get the child node of too large methods or functions. we will get the hole function / method if 
    # both the function / method and code block has been retrieved
    parent_node_ids = {}
    for node in nodes_with_score:
        if node not in not_valid_nodes_with_score:
            if node.node.parent_node_id is None or node.node.node_type != models.NodeType.CODE: continue
            if node.node.parent_node_id not in parent_node_ids:
                parent_node_ids[node.node.parent_node_id] = 1
            else:
                parent_node_ids[node.node.parent_node_id] += 1
                
    node_ids = {id for id in parent_node_ids if parent_node_ids[id] >= 1}
    return_nodes = []
    for node_with_score in nodes_with_score:
        node = node_with_score.node 
        if node not in not_valid_nodes_with_score:
            if node.parent_node_id in node_ids:
                parent_node = db.get(models.Node, node.parent_node_id)
                return_nodes.append([parent_node.id, parent_node.text, node_with_score.score, {'parent': True}])
            else:
                if node.id in node_ids: continue
                return_nodes.append([node.id, node.text, node_with_score.score, {'parent': False}])
    
    # finally, we will retrieve the most similar relation based on similarity-search. each retrieved node (up until now) will have only 1 most similar relation
    # and this is the relation that will be fed into the context
    most_similar_relationships = {}
    nodes = [db.get(models.Node, node_info[0]) for node_info in return_nodes]
    # we get the different functions / classes that appear on the retrieved nodes for more context
    relations = node_post_proccesor._check_relationships_of_retrieved_nodes(nodes=nodes, depth=1)
    relationships_nodes = {}
    for node_id in relations:
        if node_id in relationships_nodes or node_id in [node_info[0] for node_info in return_nodes]: continue
        relationships_nodes[node_id] = db.get(models.Node, node_id).text
        
    for node in nodes:
        scores_of_node = []
        ids = []
        for id, text in relationships_nodes.items():
            similarity = 1 - np.cos(np.dot(np.array(embeddings(node.text)), np.array(embeddings(text))))
            scores_of_node.append(similarity)
            ids.append(id)
        if not len(scores_of_node): continue
        most_similar_relationships[ids[np.argmax(scores_of_node)]] = [relationships_nodes[ids[np.argmax(scores_of_node)]], max(scores_of_node)]
        
    return {"nodes": return_nodes, 
            "parent_nodes": parent_node_freq, 
            "file_node": file_node_freq, 
            "most_similar_relations": most_similar_relationships, 
            "relations": relationships_nodes}
        
@app.post("/query_chatgpt")
async def query_chatgpt(request: Request, 
                        db: Session = Depends(get_db)):
    
    max_rel = 5
    node_information = await query_vector_database(request=request, db=db)
    request_json = await request.json()
    
    most_similar = request_json.get('most_similar')
    
    (retrieved_nodes, parent_of_retrieved_nodes, 
    file_of_retrieved_nodes, most_similar_relations_of_retrieved_nodes, 
    relations_of_retrieved_nodes) = [info for info in node_information.values()]
    
    if most_similar:
        max_rel = 1
    else:
        most_similar_relations_of_retrieved_nodes = relations_of_retrieved_nodes
    
    file_ids = set()
    for (file_id, _) in file_of_retrieved_nodes:
        file_ids.add(db.get(models.File, file_id).path)
        
    parent_ids = set()
    for (parent_id, _) in parent_of_retrieved_nodes:
        node_metadata = db.get(models.NodeMetadata, parent_id)
        if node_metadata:
            parent_ids.add((node_metadata.node_metadatanode_metadata))
        
        
    request_json =  await request.json()
    query = request_json['code']
    only_most_similar_relations = request_json.get('most_similar')
    
    if not only_most_similar_relations:
        only_most_similar_relations = relations_of_retrieved_nodes
     
    context_for_chatgpt = "".join([node_info[1] for node_info in retrieved_nodes])
    refine_context = "".join([rel_node[0] for m, rel_node in enumerate(most_similar_relations_of_retrieved_nodes.values()) if m < max_rel])

    # original_answer = await send_request_to_chatgpt(headers=headers, data=data)
    prompt = f"""
             You are an expert python programmer. You are very good at explaining things in a way that a complete beginer will understand. You remain technical. In your answers, you include the code you are referring to as you explain what it does so that the user will not be lost in the explanation.\n
             If you do not know how to answer the question, you will ask for more details being specific.\n
             This is the information you have to answer the user: \n 
             --------------------- CODE ------------------ \n
             {context_for_chatgpt} \n 
             {refine_context} \n 
             --------------------- CODE ------------------- \n 
             \n 
             Only use the information needed to answer the user question
            """
            
    data = {
        "model": "llama3", 
        "prompt": prompt, 
        "stream": False
    }
    
    try:
        async with httpx.AsyncClient(timeout=90) as client:
            print("Asking ollama...")
            response = await client.post("http://localhost:11434/api/generate", data=json.dumps(data)) 
            
        original_answer = response.json()['response']
    except Exception as e:
        original_answer = f"Could not get a response because of: {e}"
        print(response.json())
    
    return {"answer": original_answer, 
            "file_of_context": file_ids, 
            "parent_of_context": parent_ids, 
            "most_similar_relations": most_similar_relations_of_retrieved_nodes, 
            "nodes": retrieved_nodes}

