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

# Results

I've created a knowledge base using this respository itself! Let's see what results we get using **llama3-8b**. 

- Query: 

- Retrieved node: 

- Relationships found: 


If you see the definition of the function `_create_file_node`, you can see that other entities are being called: 
- File
- _create_nodes_of_file
- calculate_hash

Which are precisely the relationships nodes that are retrieved! Why? Because these relationships are stored on the database and can be retrieved when the node in which these entities are called is retrieved! This gives the more context, context that can be used if neccesary. This can be leveraged using several techniques: prompt engineering, llm decision making, etc. 

# Comments

When you update your code, all the files will be saved on a folder called user_code inside the folder of this cloned repository. The files will be saved according to your zip file (the operation is just an unzip function). 

**If you want to update your code, you don't need to make changes and upload the zip file again! Just make the changes inside the user_code folder, save them and click on the `Update your database` button!**. 

The changed files will be rewritten in your database and new relationships will be computed! 