import httpx
import json
import random
import asyncio 

from httpx import Timeout

from typing import List
import os
from llama_index.embeddings.huggingface import HuggingFaceEmbedding


class HugginFaceEmbeddings:
    
    def __init__(self):
        self._model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
        
    def _get_embedding_from_word(self, word: str | List[str]) -> List[float]:
        return list(self._model.get_text_embedding(word))
    
    def __call__(self, word: str | List[str]) -> List[float]:
        return self._get_embedding_from_word(word)


async def send_request_to_chatgpt(headers, data):
    
    retries = 3
    base_delay = 0.5
    
    retry_count = 0
    while retry_count <= retries:
        try:
            async with httpx.AsyncClient(timeout=Timeout(100.0, connect=100.0, read=200.0, write=100.0)) as client:
                # Make the request async using the async client.
                response = await client.post(
                    'https://api.openai.com/v1/chat/completions',
                    headers=headers,
                    data=json.dumps(data)
                )
                response.raise_for_status()  # This will raise an exception for HTTP error responses.
                result = response.json()
                answer = result['choices'][0]['message']['content']
                return answer
                
        except (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.WriteTimeout, httpx.HTTPStatusError) as e:
            # Check if the retry limit has been reached
            if retry_count == retries:
                return 
            wait_time = (base_delay * 2 ** retry_count) + (random.uniform(0, 0.1) * (2 ** retry_count))
            await asyncio.sleep(wait_time)
            retry_count += 1