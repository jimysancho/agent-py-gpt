import psycopg2
from pgvector.psycopg2 import register_vector
from sqlalchemy.orm import Session

from app.database.base import SQLALCHEMY_DATABASE_URL
from app.database.models import Node, File, NodeWithScore
from app.retrievers.base import BaseRetriever
from app.printer import Printer

from typing import (Optional, 
                    Set, 
                    Any)

printer = Printer()


class SimilarityRetriever(BaseRetriever):
        
    def __init__(self, db: Session):
        super().__init__(db=db)
        
    def _retrieve_nodes(self, query: str):
        
        embedding = self._embedding_model(word=query)
        
        conn = psycopg2.connect(SQLALCHEMY_DATABASE_URL)
        register_vector(conn)
        cur = conn.cursor()
        cur.execute("""
            SELECT id, 1 - cosine_distance(embedding, %s::vector) AS similarity 
            FROM node 
            ORDER BY similarity DESC 
            LIMIT 5;
        """, (embedding,))
        
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

    def query_database(self, query: str, subjects: Optional[Set[str]] = None) -> Any:
        
        if len(subjects) > 1:
            
            total_nodes = []
            printer.print_blue(f"Original Query: {query}")
            for subject in subjects:
                
                query_to_embed = query.replace(subject, "") if subject in query else query.lower().replace(subject, "")
                printer.print_blue(f"\tNew query to look with subject: {subject} -->  {query_to_embed}")
                nodes, _ = self._retrieve_nodes(query=query_to_embed)
                total_nodes.extend(nodes)
            
            return total_nodes
                
        if len(subjects) == 1:
            nodes, _ = self._retrieve_nodes(query=query)
            for node in nodes:
                printer.print_blue(f"Node obtainer with score: {node[2]} --> {node[1]}")
            return nodes
