import httpx
import json
import asyncio
import random 

from app.prompts.prompt import Prompt

from g4f.client import AsyncClient

class GPTClient:
    
    n_retries = 3
    _timeout = 90
    _client = AsyncClient()
    
    async def acall(self, query: str) -> str | None:
        retries = 0
        
        while retries <= self.n_retries:
            try:
                answer = await self._acall(query=query)
                return answer
            except (httpx.ConnectTimeout, httpx.ReadTimeout) as e:
                if retries == self.n_retries:
                    print("Could not get answer from llama --> Timeout")
                    raise e 
                retries += 1
                print("Could not get answer from llama because of time out. Trying again --> ", retries)
                await asyncio.sleep(random.random() * retries / 4)
            
        return None
    
    async def _acall(self, query: str) -> str: 
        
        response = await self._client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": query}]
        )
        return response
            
class LlamaClient:
    
    n_retries = 3
    _timeout = 90
        
    async def acall(self, query: str | Prompt) -> str | None:
        if not isinstance(query, str):
            query = query.prompt
            
        retries = 0
        while retries <= self.n_retries:
            try:
                answer = await self._acall(query=query)
                return answer
            except (httpx.ConnectTimeout, httpx.ReadTimeout) as e:
                if retries == self.n_retries:
                    print("Could not get answer from llama --> Timeout ")
                    raise e 
                retries += 1
                print("Could not get answer from llama because of time out. Trying again --> ", retries)
                await asyncio.sleep(random.random() * retries / 4)
            
        return None# NOTE -> mypy gives error if not
    
    async def _acall(self, query: str) -> str | None: 
        
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            data = {
                "model": "llama3:8b", 
                "prompt": query, 
                "stream": False, 
                "retries": 1
            }
            response = await client.post("http://localhost:11434/api/generate", data=json.dumps(data)) 
            response_json = response.json()
            try:
                answer = response_json['response']
            except KeyError:
                print(f"Could not get an answer from llama --> {response_json, response.status_code}")
                return None
            
        return answer
    
        