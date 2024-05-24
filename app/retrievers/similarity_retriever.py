import psycopg2
from pgvector.psycopg2 import register_vector
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database.base import SQLALCHEMY_DATABASE_URL
from app.database.models import Node, NodeWithScore, NodeMetadata
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
            nodes.append(node)
            node_with_score = NodeWithScore(node=node, score=distance)
            nodes_with_score.append(node_with_score)
            
        return nodes, nodes_with_score

    def query_database(self, query: str, subjects: Optional[Set[str]] = None, depth: Optional[int] = 1) -> Any:
                    
        total_nodes = []
        total_nodes_with_score = []
        relationships = {}
        node_of_subject = None
        printer.print_blue(f"Original Query: {query}")
        for subject in subjects:
            
            # we try to find the node in case it is a method, function or class by looking it up in the database directly
            node_of_subject = self._db.query(Node).join(NodeMetadata, NodeMetadata.node_id == Node.id)\
                .filter(
                    or_(
                        NodeMetadata.node_metadata['additional_metadata']['function_name'].astext == subject,
                        NodeMetadata.node_metadata['additional_metadata']['method_name'].astext == subject,
                        NodeMetadata.node_metadata['additional_metadata']['class_name'].astext == subject
                    )).all()

            # in case we have a match we append it and look for its relationships
            if len(node_of_subject) == 1:
                printer.print_blue(f"\tExact match of subject: {subject} in the database. --> {len(node_of_subject)}")
                total_nodes.extend(node_of_subject)
                for node in node_of_subject:
                    total_nodes_with_score.append(NodeWithScore(node=node, score=1))
                    relationships_of_node = self._retrieve_relationships(nodes=node_of_subject, depth=depth)
                    nodes_of_relationships = []
                    for rel_id in relationships_of_node:
                        nodes_of_relationships.append(self._db.get(Node, rel_id))
                    printer.print_blue(f"Relationships of node retrieve: {len(nodes_of_relationships)}")
                    relationships[str(node_of_subject[0].id)] = nodes_of_relationships
                continue
                            
            # if len(subjects) > 1 --> complex question else particular
            query_to_embed, = (query.replace(subject, "") if subject in query else query.lower().replace(subject, "")) if len(subjects) > 1 else (query,)
            printer.print_blue(f"\tNew query to look with subject: {subject} -->  {query_to_embed}")
            nodes, nodes_with_score = self._retrieve_nodes(query=query_to_embed)
            total_nodes.extend(nodes[:1])
            total_nodes_with_score.extend(nodes_with_score[:1])
            relationships_of_node = self._retrieve_relationships(nodes=total_nodes, depth=depth)
            nodes_of_relationships = []
            for rel_id in relationships_of_node:
                nodes_of_relationships.append(self._db.get(Node, rel_id))
            printer.print_blue(f"Relationships of node retrieve: {len(nodes_of_relationships)}")
            relationships[str(total_nodes[0].id)] = nodes_of_relationships
        
        # FIXME -> add threshold logic in case node_of_subject is not identified
        return total_nodes, total_nodes_with_score, relationships
