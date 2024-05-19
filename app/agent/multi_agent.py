from app.prompts.prompts import SIMPLE_VS_COMPLEX, GENERAL_VS_PARTICULAR_CONTEXT
from app.agent.agent import BaseAgent
from app.retrievers.base import BaseRetriever
from app.retrievers.general_retriever import GeneralRetriever
from app.retrievers.similarity_retriever import SimilarityRetriever

from app.agent.types import QuestionType, ContextType, Output

from typing import (List, 
                    Dict, 
                    Any)

class MultiAgent:
    
    def __init__(self, agents: List[BaseAgent]):
         
        self._agents = agents 
        
        self._output_to_tool = {
            QuestionType.COMPLEX: SimilarityRetriever, 
            QuestionType.SIMPLE: {
                ContextType.GENERAL: GeneralRetriever, 
                ContextType.PARTICULAR: SimilarityRetriever
            }
        }
                
    async def pipeline(self, **kwargs) -> BaseRetriever | None:
        """The order of actions: question_type -> context_type -> retriever"""
        
        output = None
        for agent in self._agents:
            answer = await agent.acall(**kwargs) if output is None else await agent.acall(**output.model_dump())
            print("Agent response: ", answer)
            answer_type = agent.get_variable_of_interest(result=answer)
            tool = self._output_to_tool[answer_type]
            if isinstance(tool, BaseRetriever):
                return tool
            output = self.parse_answer_into_output(question=kwargs['query'], answer=answer)
        
        return None
    
    @staticmethod
    def parse_answer_into_output(question: str, answer: Dict[str, Any] | str) -> Output:
        if not isinstance(answer, dict): answer = eval(answer)
        return Output(question=question, **answer)

  