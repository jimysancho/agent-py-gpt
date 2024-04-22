from typing import List, Tuple
from ..database.models import Node, NodeType, NodeWithScore
from sqlalchemy.orm import Session
from ..database.models import NodeMetadata, Node 
from uuid import UUID

class NodePostProccesor:
  
    def __init__(self, retrieved_nodes_score: List[NodeWithScore], db: Session, score_threshold: float=0.8, min_parent_nodes: int=2, min_file_nodes: int=1):
        
        self._retrieved_nodes_score = [node for node in retrieved_nodes_score if node.score > score_threshold]
        self._retrieved_nodes = [node.node for node in self._retrieved_nodes_score]
        
        self._score_threshold = score_threshold
        self._db = db 
        
        self._retrieved_nodes_types = self._check_retrieved_nodes_type(retrieved_nodes_score)

        self._min_parent_nodes = min_parent_nodes
        self._min_file_nodes = min_file_nodes
        
    def return_nodes_after_apply_threshold_filter(self):
        return self._retrieved_nodes
    
    def return_nodes_with_score_after_apply_threshold_filter(self):
        return self._retrieved_nodes_score
    
    def _check_retrieved_nodes_type(self, nodes: List[NodeWithScore]) -> List[NodeType]:
        _types = []
        for node in nodes:
            node_type: NodeType = node.node.node_type
            _types.append(node_type)
            
        return _types 
    
    def _check_common_parent_nodes(self) -> List[Tuple[str, int]]:
        
        parent_node_ids =  {}
        file_of_node_ids = {}
        
        for node in self._retrieved_nodes_score:
            
            node: Node = node.node 
            file_id = node.file_id
            
            if node.node_type.value == NodeType.METHOD.value or node.node_type.value == NodeType.CODE.value:
                parent_node_id = node.parent_node_id
                previous_parent_node_id = parent_node_id
                while parent_node_id is not None:
                    previous_parent_node_id = parent_node_id
                    parent_node_id = self._db.get(Node, parent_node_id).parent_node_id
                
                parent_node_id = previous_parent_node_id
                parent_node_ids[parent_node_id] = 1 if parent_node_id not in parent_node_ids else parent_node_ids[parent_node_id] + 1
            file_of_node_ids[file_id] = 1 if file_id not in file_of_node_ids else file_of_node_ids[file_id] + 1
        
        return [
            [(parent_node_id, frequency) for (parent_node_id, frequency) in parent_node_ids.items() if frequency >= self._min_parent_nodes], 
            [(file_id, frequency) for (file_id, frequency) in file_of_node_ids.items() if frequency >= self._min_file_nodes]
        ]
        
    def _check_relationships_of_retrieved_nodes(self, nodes: List[Node], depth: int) -> List[str]:

        relations = []
        for node in nodes:
            id = node.id
            node_relationships = self._db.get(Node, id).node_relationships
            if not node_relationships or not len(node_relationships): continue
            for node_relationship_id, _ in node_relationships.items():
                node_ = self._db.get(Node, node_relationship_id)
                relations.extend(self.__retrieve_relationship_nodes(base_id=id, node=node_, depth=depth-1))
                # relations.append(node_.id)
        try:
            relations = [x for x in relations if x not in [n.id for n in self._retrieved_nodes]]
        except: 
            pass 
        return relations

    def __retrieve_relationship_nodes(self, base_id: str, node: Node, depth: int):
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
    
# TODO -> take into account the number of nodes a specific file has. Maybe this is usefull to return the entire file or not 
  
  
    