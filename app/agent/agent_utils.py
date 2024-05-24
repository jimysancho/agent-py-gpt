from app.retrievers.general_retriever import GeneralRetriever
from app.retrievers.similarity_retriever import SimilarityRetriever
from app.retrievers.relationships_retriever import RelationShipRetriever

from app.agent.multi_agent import MultiAgent
from app.agent.llama_client import LlamaClient

from app.prompts.prompts import PROMPT_TO_ANSWER_QUESTIONS
from app.prompts.prompt import Prompt
from app.printer import Printer

from sqlalchemy.orm import Session

from typing import Any


printer = Printer()


async def tool_pipeline(agent: MultiAgent, query: str, db: Session) -> Any:
    tool, output = await agent.pipeline(query=query)
    tool: GeneralRetriever | SimilarityRetriever = tool(db=db)
    return tool.query_database(query=query, subjects=output.subject)
  
async def query_pipeline(agent: MultiAgent, 
                         query: str, 
                         llm: LlamaClient, 
                         db: Session, 
                         threshold: float=0.25) -> Any:
    
    tool, output = await agent.pipeline(query=query)
    tool: GeneralRetriever | SimilarityRetriever = tool(db=db)
    nodes, nodes_with_score, relationships = tool.query_database(query=query, subjects=output.subject)
    for node_with_score in nodes_with_score:
        printer.print_blue(f"Score: {node_with_score.score} for text: \n{node_with_score.node.text[:300]}\n")
    filtered_relationships = {}
    if relationships: 
        for relation, relation_nodes in relationships.items():
            for n, rel_node in enumerate(relation_nodes):
                printer.print_blue(f"\tRelationship {n+1} for node --> {relation}: \n{rel_node.text[:150]}\n")
        relationship_retriever = RelationShipRetriever(query=query, nodes=nodes, relationships=relationships)
        filtered_relationships = relationship_retriever.filter_relationships(threshold=threshold)
    context = "\n".join([node.text for node in nodes])
    context += "\n".join([node.text for relation_node in filtered_relationships.values() for node in relation_node]) if len(filtered_relationships) else ""
    prompt = Prompt.format_prompt(prompt=PROMPT_TO_ANSWER_QUESTIONS, context=context, query=query)
    answer = await llm.acall(query=prompt)
    return answer, relationships, filtered_relationships, nodes_with_score