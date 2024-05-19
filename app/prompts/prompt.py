from typing import Type

class Prompt: 
    
    def __init__(self, prompt: str):
        self._prompt = prompt
      
    @property
    def prompt(self):
        return self._prompt
    
    @classmethod  
    def format_prompt(cls, prompt: str, **kwargs) -> Type['Prompt']:
        for key, value in kwargs.items():
            prompt = prompt.replace(f"{{{key}}}", value)
        return cls(prompt=prompt)