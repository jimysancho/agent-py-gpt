import psycopg2
from pgvector.psycopg2 import register_vector
from sqlalchemy.orm import Session

from app.database.base import SQLALCHEMY_DATABASE_URL
from app.database.models import Node, File, NodeWithScore, NodeMetadata
from app.retrievers.base import BaseRetriever
from app.printer import Printer

from typing import (List, 
                    Optional, 
                    Set, 
                    Any)

printer = Printer()

class GeneralRetriever(BaseRetriever):
        
    def __init__(self, db: Session):
        super().__init__(db=db)
        
    def _retrieve_general_nodes(self) -> List[Node]:
        nodes: List[Node] = self._db.query(Node).all()
        return nodes
    
    def _retrieve_nodes(self, query: str):
        
        embedding = self._embedding_model(word=query)
        
        conn = psycopg2.connect(SQLALCHEMY_DATABASE_URL)
        register_vector(conn)
        cur = conn.cursor()
        cur.execute("""
            SELECT id, 1 - cosine_distance(embedding, %s::vector) AS similarity 
            FROM node 
            ORDER BY similarity DESC 
            LIMIT 3;
        """, (embedding,))
        
        nodes_with_distances = cur.fetchall()
        nodes = []

        for node_id, _ in nodes_with_distances:
            node = self._db.get(Node, node_id)
            nodes.append(node)
        
        return nodes
                    
    def query_database(self, query: str, subjects: Optional[Set[str]] = None) -> Any:
        
        if subjects is None: subjects = {}
        
        if len(subjects) < 1:
            nodes: List[Node] = self._retrieve_general_nodes()
            # NOTE -> what strategy to follow here
        
        elif len(subjects) > 1:
            raise ValueError("To use GeneralRetriever, the len of subjects must be one.")
        
        elif len(subjects) == 1:
            # general questions with one subject: we can assume the user is trying to get answer questions like: is my code going to break someting? If not, the tool should be particular-related one
            node_metadatas = []
            similarity_nodes: List[Node] = self._retrieve_nodes(query=query) # NOTE -> see if the others are important
            top_nodes = similarity_nodes[:2]
            valid_node = None
            
            for top_node in top_nodes:
                node_id = top_node.id
                node_metadata = self._db.get(NodeMetadata, node_id)
                if node_metadata is None: continue
                node_metadatas.append(node_metadata.node_metadata)
                metadata = node_metadata.node_metadata
                
                try:
                    metadata = metadata['additional_metadata']
                    printer.print_green(f"Metadata of the node that we're considering: {metadata}")
                except KeyError:
                    printer.print_red("This node does not have metadata...")
                    continue
                
                function_name = 'function_name' in metadata
                
                if function_name:
                    function_name = metadata.get('function_name')
                    if function_name in subjects:
                        printer.print_blue("The chosen node is a function node")
                        printer.print_blue(f"\t{node_metadata.node_metadata}")
                        valid_node = top_node
                        break
                
                method_name = metadata.get('method_name')
                if method_name in subjects:
                    printer.print_blue("The chosen node is a method node")
                    printer.print_blue(f"\t{node_metadata.node_metadata}")
                    valid_node = top_node
                    break
                
                class_name = metadata.get('class_name')
                if class_name in subjects:
                    printer.print_blue("The chosen node is a class node")
                    printer.print_blue(f"\t{node_metadata.node_metadata}")
                    valid_node = top_node
                    break

        valid_node_id = str(valid_node.id)
        all_nodes_related_to_this_node = self._db.query(Node).filter(Node.node_relationships.has_key(valid_node_id)).all()
        
        return [valid_node] + all_nodes_related_to_this_node
                    
    
# NOTE -> for a general context, we need to find all of the nodes in which the self node 
# appears. Who is the self node? -> the subject of the question. 
# we need to get this subject node with the highest probability to then look in 
# the node_relationsihps column where its id appears to retrieve that node. 
# is subject is None that is another issue. 
