from app.agent.agent import BaseAgent
from app.retrievers.base import BaseRetriever
from app.retrievers.general_retriever import GeneralRetriever
from app.retrievers.similarity_retriever import SimilarityRetriever

from app.agent.types import QuestionType, ContextType, Output
from app.printer import Printer

from typing import (List, 
                    Dict, 
                    Any, 
                    Tuple)


printer = Printer()

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
        
        self._default_tool = SimilarityRetriever
                
    async def pipeline(self, retries: int = 3, **kwargs) -> Tuple[BaseRetriever, Output] | None:
        """The order of actions: question_type -> context_type -> retriever"""
        
        output = None
        for agent in self._agents:
            answer = await agent.acall(**kwargs) if output is None else await agent.acall(**output.model_dump())
            answer_type = agent.get_variable_of_interest(result=answer)
            tool = (self._output_to_tool[answer_type] if isinstance(answer_type, QuestionType)
                    else self._output_to_tool[QuestionType.SIMPLE][answer_type])
            
            try:
                output = self._parse_answer_into_output(question=kwargs['query'], answer=answer)
            except SyntaxError:
                printer.print_red("Bad parsing from the llm. Trying again...")
                answer = await agent.acall(**kwargs) if output is None else await agent.acall(**output.model_dump())
                try:
                    output = self._parse_answer_into_output(question=kwargs['query'], answer=answer)
                except SyntaxError:
                    printer.print_red("The LLM is not acting good. Try it again later.")
                    return None
            printer.print_blue(f"Agent reasoning response: {output.reasoning}")
            printer.print_blue(f"Agent answer: {output.question_type} \n")
            
            if not output.valid:
                printer.print_red("Not valid answer. Applying retries")
                retry = 0
                while retry <= retries:
                    try:
                        output, tool = await self._apply_retry(agent=agent, **kwargs)
                        if output.valid:
                            break
                    except Exception as e:
                        printer.print_red(f"Something went wrong in the retry: {e}")
                        retry += 1
                        
                    if retry == retries:
                        printer.print_red("Could not get a coherent response. Returning default tool...")
                        return self._default_tool, output
                    retry += 1
                    
            if tool in (SimilarityRetriever, GeneralRetriever):
                type_of_tool = "SimilarityRetriever" if tool == SimilarityRetriever else "GeneralRetriever"
                printer.print_green(f"Tool decided by the agent: {type_of_tool}")
                return tool, output

        return None
    
    @staticmethod
    def _parse_answer_into_output(question: str, answer: Dict[str, Any] | str) -> Output:
        if not isinstance(answer, dict): answer = eval(answer)
        return Output(query=question, **answer)
    
    async def _apply_retry(self, agent: BaseAgent, **kwargs) -> Tuple[Output, Any]:
        answer = await agent.acall(**kwargs)
        printer.print_red(f"\tRetry agent response: {answer}")
        answer_type = agent.get_variable_of_interest(result=answer)
        tool = (self._output_to_tool[answer_type] if isinstance(answer_type, QuestionType)
                else self._output_to_tool[QuestionType.SIMPLE][answer_type])
        
        return self._parse_answer_into_output(question=kwargs['query'], answer=answer), tool
