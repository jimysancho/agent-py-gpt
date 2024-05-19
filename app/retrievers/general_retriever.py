import psycopg2
from pgvector.psycopg2 import register_vector
from sqlalchemy.orm import Session
from sqlalchemy import select

from typing import List

from app.database.base import SQLALCHEMY_DATABASE_URL
from app.database.models import Node, File, NodeWithScore
from app.retrievers.base import BaseRetriever

class GeneralRetriever(BaseRetriever):
        
    def __init__(self, query: str, db: Session):
        super().__init__(query=query, db=db)
        
    def _retrieve_nodes(self) -> List[Node]:
        nodes: List[Node] = self._db.query(Node).all()
        return nodes
    
# NOTE -> for a general context, we need to find all of the nodes in which the self node 
# appears. Who is the self node? -> the subject of the question. 
# we need to get this subject node with the highest probability to then look in 
# the node_relationsihps column where its id appears to retrieve that node. 
# is subject is None that is another issue. 
