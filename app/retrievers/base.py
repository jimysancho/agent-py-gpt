from app.embeddings import HugginFaceEmbeddings
from app.database.models import Node

from sqlalchemy.orm import Session

from abc import ABC, abstractmethod

from typing import List


class BaseRetriever(ABC):
        
    def __init__(self, db: Session):
        
        self._db = db
        self._embedding_model = HugginFaceEmbeddings()
    
    @abstractmethod
    def _retrieve_nodes(self, query: str):
        raise NotImplementedError("You need to implement _retrieve_nodes method")
    
    def _retrieve_relationships(self, nodes: List[Node], depth: int) -> List[str]:

        relations = []
        for node in nodes:
            id = node.id
            node_relationships = self._db.get(Node, id).node_relationships
            if not node_relationships or not len(node_relationships): continue
            for node_relationship_id, _ in node_relationships.items():
                node_ = self._db.get(Node, node_relationship_id)
                relations.extend(self.__retrieve_relationship_nodes(base_id=id, node=node_, depth=depth-1))
                # relations.append(node_.id)
        return relations
    
    def __retrieve_relationship_nodes(self, base_id: str, node: Node, depth: int) -> List[str]:
        if base_id == str(node.id) or depth < 1: 
            return list({base_id, node.id})
        relations = []
        node_relationships = node.node_relationships
        if not node_relationships or not len(node_relationships):
            return [node.id, base_id]
        for id, _ in node_relationships.items():
            node_ = self._db.get(Node, id)
            relations.extend(self.__retrieve_relationship_nodes(base_id=base_id, node=node_, depth=depth-1))
        return relations   

# NOTE -> Create retriever attending to the following: 
# 1. Single Cosine similarity search -> very good when the answer is particular --> high similarity
# 2. Mutiple similarity search -> when multiple subjects appear in the question but similarity still is high
# 3. General question --> create a strategy for this kind of cases (regex in the database, go one node at a time, etc)