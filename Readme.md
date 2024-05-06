# pyhthon-gpt
Chat with your python repository. 

# How to use it? 

1. docker compose up -d 
2. Go to: ```localhost:8501``` and upload your python code in a zip file. 
3. Start chatting with your repository! 

# Advantages

It leverages the python programming language syntax to improve: 
1. Chunk content
2. Relationships between nodes 

## Chunk Content

The chunk size is dynamic:
- The content of a function will be put together in the same chunk. 
- The content of a method will be put together in the same chunk. 
- Free code will be put together in the same chunk if it is found somewhere in the code. 

## Relationships

With code, the relationships `parent - child` and `prev - next` are not really usefull, because when defining big projects, there is no particular order in the code itself, so prev-next does not really make sense (only when the definition of the code is really large, for example a big function or big class). It is much more important to know: 
- If a function in a file X is called in a file Y, when the function of file Y is retrieved the function of file X should be retrieved as well so that the LLM has the complete picture of file Y. 
- If a method in some class is called somewhere else in the class, it should be noted as well. 

These are the kind of relationships that can be obtained to improve the context feeding part for the LLM. 