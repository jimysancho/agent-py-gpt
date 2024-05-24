from app.database.base import get_db, engine
from app.database import models

from app.nodes.pychunk_nodes_creation import create_nodes

from app.agent.multi_agent import MultiAgent
from app.agent.agent import ContextTypeAgent, QuestionTypeAgent
from app.agent.agent_utils import query_pipeline
from app.agent.llama_client import LlamaClient

from app.prompts.prompts import SIMPLE_VS_COMPLEX, GENERAL_VS_PARTICULAR_CONTEXT
from app.prompts.prompt import Prompt

from sqlalchemy.orm import Session
from fastapi import FastAPI, File, UploadFile
from fastapi import FastAPI, Depends, HTTPException, Request

import os, shutil
from zipfile import ZipFile

models.Base.metadata.create_all(bind=engine)
app = FastAPI()

LLAMA_URL = None# "http://host.docker.internal:11434/api/generate"


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

@app.post("/query_chatgpt")
async def query_vector_database(request: Request, db: Session = Depends(get_db)):
        
    body = await request.json()
    query = body['code']
    threshold = float(body['threshold'])
    
    # we create the multi-agent
    simple_vs_complex_prompt = Prompt(prompt=SIMPLE_VS_COMPLEX)
    simple_vs_complex_agent = QuestionTypeAgent(
        instruction=simple_vs_complex_prompt, 
        url=LLAMA_URL
    )

    # general vs particular
    general_vs_particular_prompt = Prompt(GENERAL_VS_PARTICULAR_CONTEXT)
    general_vs_particular_agent = ContextTypeAgent(
        instruction=general_vs_particular_prompt, 
        url=LLAMA_URL
        )

    multi_agent = MultiAgent(agents=[
        simple_vs_complex_agent, 
        general_vs_particular_agent
    ])
    llm = LlamaClient(url=LLAMA_URL)
    answer, relationships, filtered_relationships, nodes_with_score = await query_pipeline(agent=multi_agent, 
                                                                                           query=query, 
                                                                                           llm=llm, 
                                                                                           db=db, 
                                                                                           threshold=threshold)
    files_of_nodes = db.query(models.File)\
        .join(models.Node, models.File.id == models.Node.file_id)\
            .filter(models.Node.id.in_([node.node.id for node in nodes_with_score])).all()
    additional_metadata = {
        'files': set([file.id for file in files_of_nodes])
    }
    return_relationships = {}
    for rel, rel_nodes in relationships.items(): 
        return_relationships[rel] = {node.id: node.text[:300] for node in rel_nodes}
    return_filtered_relationships = {}
    for rel, rel_nodes in filtered_relationships.items():
        return_filtered_relationships[rel] = {node.id: node.text[:300] for node in rel_nodes} 
    return {
        'answer': answer, 
        'relationships': return_relationships, 
        'filtered_relationships': return_filtered_relationships, 
        'nodes': {node.node.id: (node.score, node.node.text) for node in nodes_with_score}, 
        'additional_medatata': additional_metadata
    }
