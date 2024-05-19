import psycopg2
from pgvector.psycopg2 import register_vector
from sqlalchemy.orm import Session

from app.database.base import SQLALCHEMY_DATABASE_URL
from app.database.models import Node, File, NodeWithScore
from app.retrievers.base import BaseRetriever

class SimilarityRetriever(BaseRetriever):
        
    def __init__(self, query: str, db: Session):
        super().__init__(query=query, db=db)
        
    def _retrieve_nodes(self):
        conn = psycopg2.connect(SQLALCHEMY_DATABASE_URL)
        register_vector(conn)
        cur = conn.cursor()
        cur.execute("""
            SELECT id, 1 - cosine_distance(embedding, %s::vector) AS similarity 
            FROM node 
            ORDER BY similarity DESC 
            LIMIT 5;
        """, (self._embedding,))
        
        nodes_with_distances = cur.fetchall()
        nodes = []
        nodes_with_score = []
        for node_id, distance in nodes_with_distances:
            node = self._db.get(Node, node_id)
            file_of_node = self._db.query(File).filter(File.id == node.file_id).first()
            nodes_with_score.append(NodeWithScore(node=node, score=distance))
            nodes.append([node.id, node.text, distance, file_of_node.path])
            
        return nodes, nodes_with_score
    
    def _navigate_trougth_relationships(self, agent):
        ...
