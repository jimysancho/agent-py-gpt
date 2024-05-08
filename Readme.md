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

### 1. Query: 
<img width="865" alt="Screenshot 2024-05-08 at 09 09 44" src="https://github.com/jimysancho/python-gpt/assets/105709376/01809b10-e0f6-4c2c-927b-df31fc8a27bb">

### 2. Retrieved node: 
<img width="834" alt="Screenshot 2024-05-08 at 09 10 14" src="https://github.com/jimysancho/python-gpt/assets/105709376/c44b4bea-233c-4470-af78-9799a82413d5">

**Perfect match**

### 3. Relationships found: 
<img width="844" alt="Screenshot 2024-05-08 at 09 10 37" src="https://github.com/jimysancho/python-gpt/assets/105709376/78688821-b13f-467a-a89c-d66f25b2c6c2">
<img width="770" alt="Screenshot 2024-05-08 at 09 13 22" src="https://github.com/jimysancho/python-gpt/assets/105709376/03bc9e6b-2bd6-41b5-9644-fe288a07f614">


If you see the definition of the function `_create_file_node`, you can see that other entities are being called: 
- File
- _create_nodes_of_file
- calculate_hash

Which are precisely the relationships nodes that are retrieved! Why? Because these relationships are stored on the database and can be retrieved when the node in which these entities are called is retrieved! This gives the more context, context that can be used if neccesary. This can be leveraged using several techniques: prompt engineering, llm decision making, etc. 

# Comments

When you update your code, all the files will be saved on a folder called user_code inside the folder of this cloned repository. The files will be saved according to your zip file (the operation is just an unzip function). 

**If you want to update your code, you don't need to make changes and upload the zip file again! Just make the changes inside the user_code folder, save them and click on the `Update your database` button!**. 

The changed files will be rewritten in your database and new relationships will be computed! 


You can also control the relationships extraction depth. What if the retrieved relationships of the retrieved node also has more relationsihps? You can go deeper to get the relationships of these relationships by controlling the depth parameter of the retriever. In `app/app.py` file: 

<img width="973" alt="Screenshot 2024-05-08 at 10 39 02" src="https://github.com/jimysancho/python-gpt/assets/105709376/9a80d56a-0842-4546-8c35-ab2b6e26d0b9">

