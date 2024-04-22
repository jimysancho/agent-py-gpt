import httpx, json, random, asyncio 
from httpx import Timeout
import os
from openai import OpenAI

openai_client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

def create_embedding(query: str):
    query = query.replace("\n", "")
    return openai_client.embeddings.create(input=[query], model='text-embedding-3-small').data[0].embedding
    
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