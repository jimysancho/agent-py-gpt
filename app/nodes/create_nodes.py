# first we are going to create module metadata and then class metadata
from ..database.models import NodeType, Node, File, NodeMetadata
import hashlib
import os , subprocess
from sqlalchemy.orm import Session
from sqlalchemy import or_
from ..openai_utils import create_embedding

MAX_NUMBER_OF_LINES_PER_BLOCK_OF_CODE = 50


class Pointer: 
    start = 'start'
    end = 'end'

class Delimiter:

    module_delimiter = {Pointer.start: "#- BEGIN MODULES -#", Pointer.end: "#- END MODULES -#"}
    function_delimiter = {Pointer.start: "#- BEGIN FUNCTION", Pointer.end: "#- END FUNCTION"}
    class_delimiter = {Pointer.start: "#- BEGIN CLASS", Pointer.end: "#- END CLASS"}
    method_delimiter = {Pointer.start: "#- BEGIN METHOD OF CLASS", Pointer.end: "#- END METHOD OF CLASS"}
    free_code_delimiter = {Pointer.start: "#- BEGIN BLOCK OF CODE -#", Pointer.end: "#- END BLOCK OF CODE -#"}

def calculate_hash(text, algorithm='sha256'):
    import random 
    hasher = hashlib.new(algorithm)
    if len(text) < 1:
        text = str(random.randint(0, 1_000_000_000_000_000))
    hasher.update(text.encode('utf-8'))
    return hasher.hexdigest()

def create_nodes_from_file(file: str):
    lines = open(file).readlines()
    modules_text = None 
    class_text = None 
    method_text = None 
    function_text = None 
    free_code = None 
        
    for line in lines:
                
        if line.startswith(Delimiter.module_delimiter[Pointer.start]):
            modules_text = []
            class_text = None
            function_text = None 
            method_text = None 
            free_code = None 
            
            begin_module_line = True  
            end_module_line = False 
        
        elif line.startswith(Delimiter.class_delimiter[Pointer.start]):
            class_text = []
            modules_text = None
            function_text = None 
            method_text = None 
            free_code = None 
            
            begin_class_line = True  
            end_class_line = False 
            class_name = line.replace(" ", "").split(":")[-1][:-3]
            
        
        elif line.startswith(Delimiter.function_delimiter[Pointer.start]):

            function_text = []
            method_text = None 
            class_text = None 
            modules_text = None 
            free_code = None 
            
            begin_function_line = True 
            end_function_line = False 
            
        elif line.startswith(Delimiter.free_code_delimiter[Pointer.start]):
            
            free_code = []
            function_text = None
            method_text = None 
            class_text = None 
            modules_text = None 
            
            begin_free_code = True 
            end_free_code = False 
    
        elif line.startswith(Delimiter.module_delimiter[Pointer.end]) and isinstance(modules_text, list):
            modules_content = "".join(modules_text)
            modules_text = None 
            end_module_line = True 
            yield modules_content, None , None, None, NodeType.MODULE, Node
            
        elif line.startswith(Delimiter.class_delimiter[Pointer.end]) and isinstance(class_text, list):
            class_metadata = class_text[0].split(":")[-1]
            begin_line, end_line = class_metadata.split("-")[-1].split(",")
            metadata = class_metadata.split(":")[-1].split("-")[0]
            del class_text[0]
            class_content = "".join(class_text)
            class_text = None 
            end_class_line = True 
            begin_class_line = False 
            yield class_content, (int(begin_line), int(end_line)), class_name, None, NodeType.CLASS, metadata
                            
        elif line.startswith(Delimiter.function_delimiter[Pointer.end]) and isinstance(function_text, list):

            end_function_line = True 
            begin_function_line = False 
            function_metadata = function_text[0]
            metadata = function_text[0].split("Arguments:")[-1].split("-")[0]
            function_name = line.split("FUNCTION:")[-1].replace(" ", "")[:-3]
            begin_line, end_line = function_metadata.split("-")[-1].split(",")
            del function_text[0]
            function_content = "".join(function_text)
            function_text = None 
            yield (function_content, 
                  (int(begin_line), 
                   int(end_line)), 
                   None, 
                   function_name, 
                   NodeType.FUNCTION, 
                   metadata)
            
        elif line.startswith(Delimiter.free_code_delimiter[Pointer.end]) and isinstance(free_code, list):
            end_free_code = True 
            begin_free_code = False 
            code_metadata = free_code[0]
            begin_line, end_line = code_metadata.split(":")[-1].split(",")
            del free_code[0]
            code_content = "".join(free_code)
            free_code = None 
            yield (code_content, 
                  (int(begin_line), 
                   int(end_line)), 
                   None, 
                   None, 
                   NodeType.CODE, 
                   None)
            
        if isinstance(modules_text, list):
            if begin_module_line: 
                begin_module_line = False 
                continue
            if end_module_line:
                continue
            
            modules_text.append(line)
            
        elif isinstance(class_text, list):
            if begin_class_line: 
                begin_class_line = False 
                continue
            if end_class_line:
                continue
            class_text.append(line)
                
        elif isinstance(function_text, list):
            if begin_function_line:
                begin_function_line = False 
                continue
            if end_function_line:
                continue
            function_text.append(line)

        elif isinstance(free_code, list):
            if begin_free_code:
                begin_free_code = False 
                continue
            if end_free_code:
                continue
            free_code.append(line)
            

    for line in lines:
                    
        if line.startswith(Delimiter.method_delimiter[Pointer.start]):
            method_text = []
            class_text = None 
            modules_text = None
            function_text = None 
            free_code = None 
            
            begin_method_line = True 
            end_method_line = False 
            
        elif line.startswith(Delimiter.method_delimiter[Pointer.end]) and isinstance(method_text, list):
            method_metadata = method_text[0]
            metadata = method_metadata.split("Arguments:")[-1].split("-")[0]
            class_name = line.split("CLASS")[-1].split(":")[0].replace(" ", "")
            method_name = line.split("CLASS")[-1].split(":")[1].replace(" ", "")[:-3]
            begin_line, end_line = method_metadata.split("-")[-1].split(",")
            del method_text[0]
            method_content = "".join(method_text)
            method_text = None 
            end_method_line = True 
            begin_method_line = False 
            yield (method_content, 
                (int(begin_line), 
                int(end_line)), 
                class_name, 
                method_name, 
                NodeType.METHOD, 
                metadata)
            
        if isinstance(method_text, list):
            if begin_method_line: 
                begin_method_line = False 
                continue
            if end_method_line:
                continue
            method_text.append(line)
            

def _create_file_node(path: str, db: Session):
    updated_files = []
    for root, _, files in os.walk(path):
        for file in files:
            lines = open(os.path.join(root, file), "r").readlines()
            text = "".join(lines)
            hash = calculate_hash(text)
            path = os.path.join(root, file)
            already_exists = db.query(File).filter(or_(File.hash == hash, File.path == path)).first()
            if already_exists:
                if db.query(File).filter(File.hash == hash).first():
                    print(f"{path} already exits")
                    continue
                else:
                    print(f"Removing file: {path} and its nodes...")
                    file = db.query(File).filter(File.path == path).first()
                    created_at = file.created_at                
                    db.delete(file)
                    db.commit()
                        
                    file = File(hash=hash, path=path, created_at=created_at)
                    db.add(file)
                    db.commit()
                    _create_nodes_of_file(path=file.path, 
                                          db=db, 
                                          file_id=file.id)
                    updated_files.append(file.path)
                    continue
                
            file = File(hash=hash, 
                        path=os.path.join(root, file))
                    
            db.add(file)
            db.commit()
            _create_nodes_of_file(path=file.path, 
                                  db=db, 
                                  file_id=file.id)
            updated_files.append(file.path)
    return updated_files
           
        
def _create_nodes_of_file(path: str, db: Session, file_id: str):
    files_structure_folder = os.environ['FILES_STRUCTURE_FOLDER']
    os.makedirs(files_structure_folder, exist_ok=True)
    
    if path.startswith("."): path = path[2:]
    elif path.startswith(".."): path = path[3:]
    
    file_name = path.replace("/", "_").split(".")[0]
    os.makedirs(files_structure_folder, exist_ok=True)
    command = f"./bash-scripts/generate-node-metadata.sh {path} {files_structure_folder}/{file_name}_info.txt > ./{files_structure_folder}/{file_name}_final.txt"
    subprocess.run(["bash", "-c", command])

    classes_names_to_uuids = {}
    for (code, 
         lines_of_code, 
         class_name, 
         function_or_method_name, 
         node_type, 
         metadata) in create_nodes_from_file(f"./{files_structure_folder}/{file_name}_final.txt"):
        
        hash = calculate_hash(text=code)
        already_exists = db.query(Node).filter(Node.hash == hash).first()
        
        if already_exists:
            continue
     
        embedding = create_embedding(code)

        node = Node(node_type=node_type, 
                    file_id=file_id, 
                    text=code, 
                    hash=hash, 
                    embedding_text_1536=embedding)
        
        db.add(node)
        db.commit()

        if node_type == NodeType.FUNCTION or node_type == NodeType.METHOD or node_type == NodeType.CODE:
            if abs(int(lines_of_code[1]) - int(lines_of_code[0])) >= MAX_NUMBER_OF_LINES_PER_BLOCK_OF_CODE:
                lines = code.split("\n")
                prev_node = None 

                for k in range(0, len(lines), MAX_NUMBER_OF_LINES_PER_BLOCK_OF_CODE):
                        
                    piece_of_code_lines = lines[k: k + MAX_NUMBER_OF_LINES_PER_BLOCK_OF_CODE]
                    piece_of_code = "".join(piece_of_code_lines)
                    node_hash = calculate_hash(piece_of_code)
                    node_embedding = create_embedding(query=piece_of_code)
                    new_node = Node(node_type=NodeType.CODE, 
                                    file_id=file_id, 
                                    parent_node_id=node.id, 
                                    text=piece_of_code, 
                                    hash=node_hash, 
                                    embedding_text_1536=node_embedding)
                    
                    db.add(new_node)
                    db.commit()
                    
                    if prev_node is not None:
                        prev_node_id = prev_node.id 
                        next_node_id = new_node.id 
                        
                        prev_node.next_node_id = next_node_id 
                        new_node.previous_node_id = prev_node_id 
                        
                        db.commit()
                    
                    prev_node = new_node 
            
        if node_type == NodeType.CLASS:
            classes_names_to_uuids[class_name.replace(" ", "")] = node.id 
            uuid_of_parent_node = None 
            node_metadata = NodeMetadata(node_id=node.id, 
                                    node_metadata={'class_name': class_name, 
                                                  'lines_of_code': lines_of_code, 
                                                  'parent_class': metadata})
            db.add(node_metadata)
            db.commit()
        elif node_type == NodeType.METHOD:
            uuid_of_parent_node = classes_names_to_uuids[class_name.replace(" ", "")]
            node.parent_node_id = uuid_of_parent_node
            node_metadata = NodeMetadata(node_id=node.id, 
                                         node_metadata={
                                             'method_name': function_or_method_name, 
                                             'lines_of_code': lines_of_code, 
                                             'arguments': metadata
                                         })
            
            db.add(node_metadata)
            db.commit()
            
        elif node_type == NodeType.FUNCTION:

            node_metadata = NodeMetadata(node_id=node.id, 
                                         node_metadata={'function_name': function_or_method_name, 
                                                        'lines_of_code': lines_of_code,
                                                        'arguments': metadata})
            
            db.add(node_metadata)
            db.commit()
        
        elif node_type == NodeType.CODE:
            node_metadata = NodeMetadata(node_id=node.id, 
                                         node_metadata={'lines_of_code': lines_of_code})
            db.add(node_metadata)
            db.commit()
                    
def _create_node_relationships_file(db: Session, delete_all_first=False):
    
    fields = ('class_name', 'function_name', 'method_name')
    name_file = os.environ['NAMES_FILE']
    relationships_file = os.environ['RELATIONSHIPS_FILE']
    
    if os.path.exists(name_file):
        os.remove(name_file)
    
    nodes = []
    for field in fields:
        nodes_metadata = db.query(NodeMetadata)\
            .filter(NodeMetadata.node_metadata[field].astext != None).all()
            
        nodes.extend(nodes_metadata)
        
        with open(name_file, "w") as names_file:
            for node in nodes:
                node_metadata: NodeMetadata = node.node_metadata
                for field in fields:
                    name = node_metadata.get(field)
                    if name is None or name == "__init__": continue
                    names_file.write(f"{name} {node.node_id} \n")
    
    command = f"./bash-scripts/find-node-relationships.sh {name_file} > {relationships_file}" 
    subprocess.run(["bash", "-c", command])
    
    if not os.path.exists(relationships_file):
        raise ValueError(f"You need to create the relationships file first")
    
    with open(relationships_file, "r") as node_relationship_file:
        lines = node_relationship_file.readlines()
        
    if delete_all_first:
        print("Setting the relationships to None...")
        db.query(Node).update({'node_relationships': None})
        db.commit()
    
    start = False 
    for line in lines:
        if line.startswith("#- BEGIN"): 

            start = True
            node_id = line.split(" ")[-2]
            
        elif line.startswith("#- END"): 
            start = False
            
        if start: 
            file_path = "./" + line.split(":")[-1].split("-")[0].replace(" ", "")
            if "#" in file_path: continue
            
            line_of_code = line.split(":")[-1].split("-")[-1].replace(" ", "")                    
            file_id = db.query(File.id).filter(File.path == file_path).first()[0]
            nodes_of_file = db.query(NodeMetadata).join(Node)\
                .filter(Node.file_id == file_id).all()
                            
            for node in nodes_of_file:
                
                node_relationships = db.get(Node, node.node_id).node_relationships                    
                lines_of_code = node.node_metadata.get('lines_of_code')
                                
                is_node_child = str(db.get(Node, node_id).parent_node_id) == str(node.node_id)
                if lines_of_code is None or is_node_child: continue
                
                if int(lines_of_code[0]) <= int(line_of_code) <= int(lines_of_code[1]):
                    
                    if node_relationships is None: 
                        node_relationships = {node_id: [int(line_of_code)]}
                    else:
                        if node_id in node_relationships:
                            try:
                                node_relationships[node_id].remove(int(line_of_code))
                            except:
                                pass
                            # finally:
                            #     node_relationships[node_id].append(int(line_of_code))
                        else:
                            node_relationships[node_id] = [int(line_of_code)]
                                    
                    if node_id in node_relationships and node_id == str(node.node_id):
                        del node_relationships[node_id]
                    
                    if not len(node_relationships): node_relationships = None 
                    db.query(Node).filter(Node.id == node.node_id).update(values={'node_relationships': node_relationships})
                    db.commit()
                            
    return {'msg': "The node relationsihps have been updated"}
