from typing import (List, 
                    Dict)

from pychunk.chunkers.python_chunker import PythonChunker

from pychunk.nodes.base import (BaseNode, 
                                NodeRelationshipType)

from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database.models import (Node, 
                                 NodeMetadata, 
                                 File)

from app.embeddings import HugginFaceEmbeddings

import hashlib
import random


def calculate_hash(text, algorithm='sha256'):

    hasher = hashlib.new(algorithm)
    if len(text) < 1:
        text = str(random.randint(0, 1_000_000_000_000_000))
    hasher.update(text.encode('utf-8'))
    return hasher.hexdigest()

def create_nodes(path: str, db: Session) -> List[str]:
    chunker = PythonChunker(files_path=path)
    hugging_face_embeddings = HugginFaceEmbeddings()
    
    nodes: Dict[str, Dict[str, BaseNode]] = chunker.find_relationships()
    created_nodes_from_file = []
    
    for file_path, nodes_of_file in nodes.items():
        lines = open(file_path).readlines()
        text = "".join(lines)
        hash = calculate_hash(text)
        already_exists = db.query(File).filter(or_(File.hash == hash, File.path == file_path)).first()
        if already_exists:
            if db.query(File).filter(File.hash == hash).first():
                print(f"{path} already exits")
                continue
        file = File(hash=hash, 
                    path=file_path)
                    
        db.add(file)
        db.flush()
        
        for node_id, node in nodes_of_file.items():
            node: BaseNode
            embedding = hugging_face_embeddings(word=node.content)
            node_relationships = node.filter_relationships(NodeRelationshipType.OTHER)
            parent_node_id = list(node.filter_relationships(NodeRelationshipType.PARENT).keys())
            if len(parent_node_id):
                parent_node_id, = parent_node_id
            else:
                parent_node_id = None
                
            node_db: Node = Node(
                id=node_id, 
                file_id=file.id, 
                node_type=node.node_type, 
                hash=node.metadata['hash'], 
                text=node.content, 
                parent_node_id=parent_node_id, 
                embedding=embedding, 
                node_relationships=node_relationships
            )
            db.add(node_db)
            db.flush()
            
            # NodeMetadata
            node_metadata = NodeMetadata(
                node_id=node.id, 
                node_metadata={**node.metadata}
            )
            
            db.add(node_metadata)
            db.commit()
            
        created_nodes_from_file.append(file_path)
        
    return created_nodes_from_file