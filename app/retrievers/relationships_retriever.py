# NOTE -> create some kind of logic to determine what relationships are really useful. Maybe compare the original node text with the relationship text + query or something like that. 
# With agents I don't think the result will be good but try it anyway. 
from app.database.models import Node
from app.embeddings import HugginFaceEmbeddings
from app.printer import Printer

from typing import Dict, List, Any
import numpy as np

printer = Printer()

class RelationShipRetriever:

    def __init__(self, query: str, nodes: List[Node], relationships: Dict[str, List[Node]]):
        self._query = query
        self._relationships = relationships
        self._n_relationships = 0
        for _, rel_nodes in self._relationships.items():
            self._n_relationships += len(rel_nodes)
            
        self._nodes = nodes
        
        self._embeddings = HugginFaceEmbeddings()
        
    def filter_relationships(self, threshold: float) -> Dict[str, List[Node]] | Dict:
        filtered_relationships = {}
        for node in self._nodes:
            for rel, rel_nodes in self._relationships.items():
                filtered_nodes = []
                for rel_node in rel_nodes:
                    similarity = 1 - np.dot(
                        np.array(node.embedding), 
                        np.array(self._embeddings(rel_node.text))
                        ) / (np.linalg.norm(np.array(node.embedding)) * np.linalg.norm(np.array(self._embeddings(rel_node.text))))
                    if similarity > threshold:
                        filtered_nodes.append(rel_node)
                filtered_relationships[rel] = filtered_nodes
        
        n_filtered = 0
        for _, n in filtered_relationships.items():
            n_filtered += len(n)
    
        printer.print_blue(f"\tFiltered relationships -> Before filtering: {self._n_relationships}. After: {n_filtered}")
        return filtered_relationships
