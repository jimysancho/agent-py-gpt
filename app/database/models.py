from app.database.base import Base 
from sqlalchemy import Column, Enum, String, Text, DateTime, ForeignKey, Index 
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, backref
from pgvector.sqlalchemy import Vector
import sqlalchemy
from pychunk.nodes.base import NodeType

import uuid, enum
    

class File(Base):

    __tablename__ = "file"
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    hash = Column(String, nullable=False, index=True, unique=True)
    path = Column(String, nullable=False, index=True, unique=True)
    created_at = Column(DateTime, nullable=False, server_default=sqlalchemy.func.now(), onupdate=sqlalchemy.func.now())
    updated_at = Column(DateTime, nullable=False, server_default=sqlalchemy.func.now(), onupdate=sqlalchemy.func.now())

    nodes = relationship("Node", back_populates="file", cascade="all, delete-orphan")
    
class NodeMetadata(Base):
    __tablename__ = "node_metadata"
    node_id = Column(UUID(as_uuid=True), ForeignKey("node.id", ondelete="CASCADE"), primary_key=True)
    node_metadata = Column(JSONB)
    # possible field for node_metadata: parent_class, lines_of_code, etc
    
    node = relationship("Node", foreign_keys=[node_id], back_populates="node_metadata")

class Node(Base):

    __tablename__ = "node"
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    node_type = Column(Enum(NodeType), nullable=False)
    file_id = Column(UUID, ForeignKey("file.id", ondelete='CASCADE'), nullable=False)
    
    parent_node_id = Column(UUID(as_uuid=True), ForeignKey("node.id"), nullable=True)
    previous_node_id = Column(UUID(as_uuid=True), ForeignKey("node.id"), nullable=True)
    next_node_id = Column(UUID(as_uuid=True), ForeignKey("node.id"), nullable=True)
    
    text = Column(Text, nullable=False)
    embedding_text_1536 = Column(Vector(1536))
    hash = Column(String, nullable=False, index=True)
    node_relationships = Column(JSONB)
    
    parent = relationship("Node",foreign_keys=[parent_node_id],
                          remote_side=[id],
                          backref=backref("children", cascade="all, delete-orphan"))
    previous = relationship("Node", foreign_keys=[previous_node_id], remote_side=[id], backref=backref("next_node"), uselist=False)
    next = relationship("Node", foreign_keys=[next_node_id], remote_side=[id], backref=backref("previous_node"), uselist=False)
    
    file = relationship("File", back_populates="nodes", foreign_keys=[file_id])
    node_metadata = relationship("NodeMetadata", back_populates="node", cascade="all, delete-orphan")
        
index = Index(
    'node_search_index',
    Node.embedding_text_1536,
    postgresql_using='ivfflat',
    postgresql_with={'lists': 100},
    postgresql_ops={'embedding': 'vector_l2_ops'}
)

class NodeWithScore:
    
    def __init__(self, node: Node, score: float):
        self.node = node 
        self.score = score 