from app.embeddings import HugginFaceEmbeddings
from sqlalchemy.orm import Session

from abc import ABC, abstractmethod


class BaseRetriever(ABC):
        
    def __init__(self, query: str, db: Session):
        
        self._query = query 
        self._db = db
        self._embedding_model = HugginFaceEmbeddings()
        self._embedding = self._embedding_model(query)
    
    @abstractmethod
    def _retrieve_nodes(self):
        raise NotImplementedError("You need to implement _retrieve_nodes method")
    
# NOTE -> Create retriever attending to the following: 
# 1. Single Cosine similarity search -> very good when the answer is particular --> high similarity
# 2. Mutiple similarity search -> when multiple subjects appear in the question but similarity still is high
# 3. General question --> create a strategy for this kind of cases (regex in the database, go one node at a time, etc)