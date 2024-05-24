# NOTE -> With agents I don't think the result will be good but try it anyway. 
from app.database.models import Node
from app.embeddings import HugginFaceEmbeddings
from app.printer import Printer

from sqlalchemy.orm import Session

from typing import Dict, List
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
        
    def _check_if_parent_node_is_in_relationships(self, db: Session, relationships: Dict[str, List[Node]]) -> Dict[str, List[Node]]:
        """Count the number of child nodes that appear and compare it to the actual number of child nodes a parent node has. If the number
        is high, return the parent_node and remove the child nodes, or remove the parent node and return the child nodes"""
        parent_node_ids = {}
        ids = {}
        printer.print_blue(f"\tIngoing relationships: {relationships}")
        for rel_id, rel_nodes in relationships.items():
            parent_node_ids[rel_id] = set()
            ids[rel_id] = set()
            for node in rel_nodes:
                parent_node_id = node.parent_node_id
                if parent_node_id:
                    parent_node_ids[rel_id].add(parent_node_id)
                ids[rel_id].add(node.id)

        print(parent_node_ids)
        filtered_parent_child_relationships: Dict[str, List[Node]] = {}
        for rel_id, parent_ids in parent_node_ids.items():
            filtered_parent_child_relationships[rel_id] = []
            for parent_id in parent_ids:
                childs = db.query(Node).filter(Node.parent_node_id == parent_id).all()
                childs_retrieved = [child for child in childs if child.id in ids[rel_id]]
                retrieved_proportion = len(childs_retrieved) / len(childs)
                printer.print_blue(f"\tProportion of child nodes retrieved: {retrieved_proportion}")
                if retrieved_proportion >= 0.5:
                    parent_node = db.query(Node).filter(Node.id == parent_id).first()
                    filtered_parent_child_relationships[rel_id].append(parent_node)
                    nodes = relationships[rel_id]
                    for node in nodes:
                        if node not in childs_retrieved:
                            filtered_parent_child_relationships[rel_id].append(node)
                    
                    printer.print_blue(f"\tWe have removed: {len(relationships[rel_id]) - len(filtered_parent_child_relationships[rel_id])} nodes by adding the parent.")
                else:
                    filtered_parent_child_relationships[rel_id] = relationships[rel_id]
        
        printer.print_blue(f"\tOutgoing relationships: {filtered_parent_child_relationships}")
        return filtered_parent_child_relationships
        
                
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