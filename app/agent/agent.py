from app.prompts.prompt import Prompt

from app.retrievers.base import BaseRetriever
from app.agent.llama_client import LlamaClient
from app.agent.types import QuestionType, ContextType

from abc import ABC, abstractmethod
from typing import (Optional,
                    List, 
                    Any)

import re


class BaseAgent(ABC):
    
    def __init__(self, 
                 instruction: Prompt):
        
        self._instruction = instruction
        self._client = LlamaClient()
        
    @abstractmethod
    async def acall(self, **kwargs):
        raise NotImplementedError("You need to implement acall")
    
    @abstractmethod
    def get_variable_of_interest(self, result: str) -> Any:
        raise NotImplementedError("You need to implement get_variable_of_interest")
    

class QuestionTypeAgent(BaseAgent):
    
    def __init__(self, instruction: Prompt):
        super().__init__(instruction=instruction)
        
    async def acall(self, **kwargs) -> str | None:
        query = self._instruction.format_prompt(prompt=self._instruction.prompt, **kwargs).prompt
        print(f"QuestionTypeAgent --> {query}")
        return await self._client.acall(query=query)
    
    def get_variable_of_interest(self, result: str) -> QuestionType | None:
        
        try:
            dict_result = eval(result.strip())
            question_type = dict_result['question_type']
            return QuestionType.SIMPLE if question_type == 'simple' else QuestionType.COMPLEX
        except Exception as e:
            print(f"Bad parsing from the llm -> {e}")
            pattern = r'"question_type": "(\w+)"'
            groups = re.findall(pattern, result)
            if not groups:
                print("Bad parsing in general: ", result)
                return None
            return QuestionType.SIMPLE if groups[0] == 'simple' else QuestionType.COMPLEX
    

class ContextTypeAgent(BaseAgent):
    
    def __init__(self, 
                 instruction: Prompt):
        super().__init__(instruction=instruction)
        
    async def acall(self, **kwargs) -> str | None:
        query = self._instruction.format_prompt(prompt=self._instruction.prompt, **kwargs).prompt
        print(f"ContextTypeAgent --> {query}")
        return await self._client.acall(query=query)
    
    def get_variable_of_interest(self, result: str) -> ContextType | None:
        
        try:
            dict_result = eval(result.strip())
            question_type = dict_result['question_type']
            return ContextType.PARTICULAR if question_type == 'particular' else ContextType.GENERAL
        except Exception as e:
            print(f"Bad parsing from the llm -> {e}")
            pattern = r'"question_type": "(\w+)"'
            groups = re.findall(pattern, result)
            if not groups:
                print("Bad parsing in general: ", result)
                return None
            return ContextType.PARTICULAR if groups[0] == 'particular' else ContextType.GENERAL
