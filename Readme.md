# Table of Contents
[Introduction](https://github.com/jimysancho/agent-py-gpt/tree/agent-main?tab=readme-ov-file#chat-with-your-python-repository-in-an-advanced-way)

[Chunking and Node Models](https://github.com/jimysancho/agent-py-gpt/tree/agent-main?tab=readme-ov-file#1-chunking-and-node-models)

[Tools](https://github.com/jimysancho/agent-py-gpt/tree/agent-main?tab=readme-ov-file#2-tools)

- [SimpleRetriever](https://github.com/jimysancho/agent-py-gpt/tree/agent-main?tab=readme-ov-file#21-simpleretriever)

    - - [Complex Case](https://github.com/jimysancho/agent-py-gpt/tree/agent-main?tab=readme-ov-file#211-complex-case)

- [GeneralRetriever](https://github.com/jimysancho/agent-py-gpt/tree/agent-main?tab=readme-ov-file#22-generalretriever)
    - - [One Subject](https://github.com/jimysancho/agent-py-gpt/tree/agent-main?tab=readme-ov-file#221-one-subject)

    - - [Zero Subjects](https://github.com/jimysancho/agent-py-gpt/tree/agent-main?tab=readme-ov-file#222-zero-subjects)
- [RelationshipRetriever](https://github.com/jimysancho/agent-py-gpt/tree/agent-main?tab=readme-ov-file#23-relationshipretriever-optional-or-mandatory)
    - - [Without Relationships in the context](https://github.com/jimysancho/agent-py-gpt/tree/agent-main?tab=readme-ov-file#231-without-the-relationships)

    - - [With Relationships in the context](https://github.com/jimysancho/agent-py-gpt/tree/agent-main?tab=readme-ov-file#232-with-the-relationships-in-the-context)

    - - [Differences](https://github.com/jimysancho/agent-py-gpt/tree/agent-main?tab=readme-ov-file#233-differences)

[Main files](https://github.com/jimysancho/agent-py-gpt/tree/agent-main?tab=readme-ov-file#3-main-files)

- [Notebooks examples](https://github.com/jimysancho/agent-py-gpt/tree/agent-main?tab=readme-ov-file#31-notebooks-examples) 

- [Classes](https://github.com/jimysancho/agent-py-gpt/tree/agent-main?tab=readme-ov-file#32-classes)


[How to use it](https://github.com/jimysancho/agent-py-gpt/tree/agent-main?tab=readme-ov-file#4-how-to-use-it)

[Comments](https://github.com/jimysancho/agent-py-gpt/tree/agent-main?tab=readme-ov-file#comments)

[Problems](https://github.com/jimysancho/agent-py-gpt/tree/agent-main?tab=readme-ov-file#problems)

- [Pgvector](https://github.com/jimysancho/agent-py-gpt/tree/agent-main?tab=readme-ov-file#1-pgvector-on-docker)

# Chat with your python repository in an advanced-way

The idea of this project is to use Agents to improve the RAG pipeline over python repositories. Why over python repositories? Because I'm going to use the [`rag-pychunk`](https://github.com/jimysancho/rag-pychunk) library to obtain better relationships between them. Also, this project uses Postgresql to store the vectors and documents, but you can implement the same logic in any database. The important part is the parsing form *rag-pychunk-Nodes* to your model, maintaining and keeping the important information (as we'll see in section 2, we'll try to get the node by matching some values in the database). 

In order to use agents, I've classified the possible queries into different categories: 
- Simple vs Complex. 
- If Simple: Particular vs Complex. 

What decides into which category the query falls into is the number of *subjects*. `What is a subject?` $\implies$ Any Python function, method, class or block of code. 

In order to classify the query, I've developed two different types of agents, which will return different types of tools depending on the task. Both of the agents have been trained using `prompt engineer few shot example` since the task is "straightforward", altough we'll see that it can get tricky and complicated depending on the query. The agents are:  

1. **Simple vs Complex Agent**. This agent will classify the query of the user into one of these categories: 

- Simple:  Zero or one subject present in the question. *Example: How does the function x work?*
- Complex: More than one subject.  *Example: What are the differences between Class A and Class B?*

- Tool returned: **`SimilarityRetriever`**


2. **General vs Particular Agent**. This agent will take the output from the first agent only if the question type was: **`Simple`** and classify the question into one of two categories: 

- Particular: The question involves only the subject. *Example: How does the function x work?*
- General: The question is formulated in such a way that the question does not have to do only with the subject. *Will my changes break anything?*

- Tool returned: **`SimilarityRetriever`** (for particular) or **`GeneralRetriever`** (for general)

When the agent pipeline returns a tool, I'll use that tool to obtained the nodes which will be used to fed the LLM. Let's see the hole process. 

## 1. Chunking and Node models

To chunk the different files I'll be using *rag-pychunk*, which is a library I've developed to leverage python programming language syntax improving the chunking and relationship finding. You can learn more about that here: [rag-pychunk](https://github.com/jimysancho/rag-pychunk)


**Node Model**
```
class Node(Base):

    __tablename__ = "node"
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    node_type = Column(Enum(NodeType), nullable=False)
    file_id = Column(UUID, ForeignKey("file.id", ondelete='CASCADE'), nullable=False)
    
    parent_node_id = Column(UUID(as_uuid=True), ForeignKey("node.id"), nullable=True)
    previous_node_id = Column(UUID(as_uuid=True), ForeignKey("node.id"), nullable=True)
    next_node_id = Column(UUID(as_uuid=True), ForeignKey("node.id"), nullable=True)
    
    text = Column(Text, nullable=False)
    embedding = Column(Vector(384))
    hash = Column(String, nullable=False, index=True)
    node_relationships = Column(JSONB)
    
    parent = relationship("Node",foreign_keys=[parent_node_id],
                          remote_side=[id],
                          backref=backref("children", cascade="all, delete-orphan"))
    previous = relationship("Node", foreign_keys=[previous_node_id], remote_side=[id], backref=backref("next_node"), uselist=False)
    next = relationship("Node", foreign_keys=[next_node_id], remote_side=[id], backref=backref("previous_node"), uselist=False)
    
    file = relationship("File", back_populates="nodes", foreign_keys=[file_id])
    node_metadata = relationship("NodeMetadata", back_populates="node", cascade="all, delete-orphan")
        
```

**NodeMetadata Model**
```
class NodeMetadata(Base):
    __tablename__ = "node_metadata"
    node_id = Column(UUID(as_uuid=True), ForeignKey("node.id", ondelete="CASCADE"), primary_key=True)
    node_metadata = Column(JSONB)
    
    node = relationship("Node", foreign_keys=[node_id], back_populates="node_metadata")
```

In the node_metadata column of the NodeMetadata model, some key-value pairs will be stored for each node. For example: 
```
{'method_name': <name of the method if the node is a method>}
{'class_name': <name of the class if the node is a class>}
{'function_name': <name of the function if the node is a function>}
```

In the node_relationships column of the Node Model will be stored in the form of: 
```
{node_id: [lines in which the node appears]}
```
where node_id is the nodes that appears in an specific node. For example: 
```
text_of_node_1 = "def hello(): ..."
text_of_node_2 = "def bye(): hello(); print("bye!")"
relationships_of_node_2 = {'id of node 1': [line 1]}
```

These two columns will be leveraged to improve the retrieval as we'll in the next section. 

## 2. Tools

What the agent will return depending on the query. There are 2 types of retriever that the agent will return, but there is an additional one which can be used to improve the results. 

### 2.1 SimpleRetriever

This retriever will be used when the query is identified as *particular* or *complex*. Depending on this case, the retrieval will be done differently. 

For each subject, we'll try to get the Node in which the subject appears directly from the database, since in the column *node_metadata* we are storing either the method, function or class name of the node: 

```
for subject in subjects: # complex case --> multiple subjects
            
  # we try to find the node in case it is a method, function or class by looking it up in the database directly
  node_of_subject = self._db.query(Node).join(NodeMetadata, NodeMetadata.node_id == Node.id)\
      .filter(
          or_(
              NodeMetadata.node_metadata['additional_metadata']['function_name'].astext == subject,
              NodeMetadata.node_metadata['additional_metadata']['method_name'].astext == subject,
              NodeMetadata.node_metadata['additional_metadata']['class_name'].astext == subject
          )).all()
```

If this fails, we'll get the nodes via similarity search. Either way, we'll get the relationships of the retrieved nodes. 

#### 2.1.1 Complex case
In case we have multiple subjects and the node can't be obtained directly from the database we want to maximise the probability of getting the correct nodes via similarity search. In order to do so, we modify the query like this: 
```
query_to_embed, = (query.replace(subject, "") if subject in query else query.lower().replace(subject, "")) if len(subjects) > 1 else (query,)
```

That way, only the subject name will appear in the query for each subject, removing the similarity with other nodes. 

### 2.2 GeneralRetriever

With this tool we want to answer queries like: "Will changing X break something?", "What will happen If I change this parameter of the function X to...?", "Is there any errors in the repo?"

#### 2.2.1 One subject
So, we need to get the proper node and everything that is depending on it. Again, we'll try to get the node directly from the database based on the subject name and if it does not succeed via similarity search. Besides that, we also want to get all of the nodes which in the column: *node_relationships* has the id of this node.

```
all_nodes_related_to_this_node = self._db.query(Node).filter(Node.node_relationships.has_key(str(valid_node.id))).all()
```

Where *valid_node.id* is the retrieved node. 

#### 2.2..2 Zero subjects

If no subjects are detected, then all of the nodes are retrieved and will need to be parsed one by one (maybe with its relationships to give the LLM more context) to answer the query for each and every one of them. 

### 2.3 RelationshipRetriever (Optional. Or mandatory?)
This retriever is not available for the agent to return. We'll need to use it as a postprocessor. 


With this "retriever" the relationshps will be filtered to only keep those similar to the retrieved nodes given a threshold: 

```
def filter_relationships(self, threshold: float) -> Dict[str, List[Node]] | Dict:
    filtered_relationships = {}
    for node in self._nodes:
        for rel, rel_nodes in self._relationships.items():
            filtered_nodes = []
            for rel_node in rel_nodes:
                similarity = 1 - np.cos(
                    np.dot(
                        np.array(node.embedding), 
                        np.array(self._embeddings(rel_node.text))
                    )
                )
                if similarity > threshold:
                    filtered_nodes.append(rel_node)
            filtered_relationships[rel] = filtered_nodes
```

**Does it improve the answer?** $\implies$ Let's see the difference between the answer with relationships and without relationships: 

#### 2.3.1 Without the relationships

- `Query`: How do the methods: _check_common_parent_nodes, _check_relationships_of_retrieved_nodes, return_nodes_after_apply_threshold_filter and return_nodes_with_score_after_apply_threshold_filter work together to improve the result of the function query_vector_database?
- `Answer`: 
```md
I'd be happy to help you understand how these methods work together!
To answer your question, let's focus on what these methods do:
1. _check_common_parent_nodes(): This method seems to analyze the retrieved nodes and calculates some frequency values
(parent_node_freq and file_node_freq) based on their relationships.
2. _check_relationships_of_retrieved_nodes(depth=3): This method likely checks the relationships between the retrieved nodes, possibly up to
a certain depth (in this case, 3).
3. return_nodes_after_apply_threshold_filter(): This method appears to filter the retrieved nodes based on some threshold criteria,
perhaps related to their scores.
4. return_nodes_with_score_after_apply_threshold_filter(): Similarly, this method filters the nodes with their corresponding scores, likely applying the
same threshold as above.
Now, let's consider how these methods work together:
The _check_common_parent_nodes() and _check_relationships_of_retrieved_nodes() methods seem to analyze the relationships between the retrieved nodes. The
results from these methods (parent_node_freq and file_node_freq) are then used in some way to improve
the result of the query_vector_database function.
The return_nodes_after_apply_threshold_filter() and return_nodes_with_score_after_apply_threshold_filter() methods, on the other hand, seem to refine the retrieved nodes
based on their scores. The results from these methods are also used to improve the
final result.
In summary, these methods work together by:
- Analyzing relationships between retrieved nodes
- Refining nodes based on their scores and threshold criteria
- Improving the overall result of the query_vector_database function
By combining these methods, the function can likely improve its accuracy in retrieving relevant nodes
for a given query.
```

#### 2.3.2 With the relationships in the context

- `Query`: How do the methods: _check_common_parent_nodes, _check_relationships_of_retrieved_nodes, return_nodes_after_apply_threshold_filter and return_nodes_with_score_after_apply_threshold_filter work together to improve the result of the function query_vector_database?

- `Answer`: 
```md
A Python expert!
Let's break down how these methods work together to improve the result of the query_vector_database function:
- Overview
The NodePostProccesor class is designed to process and filter nodes from a database. The four methods you mentioned are part of this processing pipeline.
1. Method 1: _check_common_parent_nodes
This method takes the retrieved nodes and checks for common parent nodes (methods) and files.
It returns a list of tuples containing the parent node IDs and their frequencies.
2. Method 2: _check_relationships_of_retrieved_nodes
This method recursively explores the relationships between nodes, starting from each node in the retrieved_nodes list. For each node, it checks its relationships (i.e., child nodes) and adds them to a list. The recursion depth is controlled by the depth parameter.
3. Method 3: return_nodes_after_apply_threshold_filter. This method simply returns the filtered nodes (_retrieved_nodes) that passed the threshold score filter.
4. Method 4: return_nodes_with_score_after_apply_threshold_filter. This method returns the original nodes with scores (_retrieved_nodes_score) that passed the threshold score filter.
This is useful for retaining the original node scores for further processing or analysis.

- How they work together
Here's how these methods contribute to improving the result of query_vector_database:
1. _check_common_parent_nodes: By identifying common parent nodes and files, you can prune the node graph and focus on more relevant nodes.
2. _check_relationships_of_retrieved_nodes: This method recursively explores relationships between nodes, which helps to identify more connected nodes (e.g., methods with similar functionality).
3. return_nodes_after_apply_threshold_filter and return_nodes_with_score_after_apply_threshold_filter: These methods filter out nodes that don't meet the threshold score, ensuring only relevant nodes are retained.
By combining these methods, you can:
* Prune the node graph to focus on more relevant nodes
* Identify connected nodes (e.g., methods with similar functionality)
* Retain only nodes that meet a certain threshold score
This processing pipeline helps to improve the result of query_vector_database by filtering out irrelevant nodes
and retaining only the most meaningful ones.
```
#### 2.3.3 Differences?

Clearly! As we can see, without the relationships the LLM just guess what the functions do, whereas when the relationships are used, it actually has the definition of the function, so it does not have to guess anymore!


Another agent could be used here to decide if the relationship is relevant to the query or not. 

# 3. Main files

## 3.1 Notebooks examples
- [`main.ipynb`](https://github.com/jimysancho/agent-py-gpt/blob/agent-main/main.ipynb): here you can find end-to-end explanations of how this multi-agent project is implemented. 
- [`0_subjects.ipynb`](https://github.com/jimysancho/agent-py-gpt/blob/agent-main/0_subjects.ipynb): an example of a question with 0 subjects answered. 
- [`relationship_retriever_example.ipynb`](https://github.com/jimysancho/agent-py-gpt/blob/agent-main/relationship_retriever_example.ipynb): to showcase how the relationships can be leveraged to improve the results. 

## 3.2 Classes

- [Retrievers](https://github.com/jimysancho/agent-py-gpt/tree/agent-main/app/retrievers): The implementation of all of the retrievers. 
- [Agents](https://github.com/jimysancho/agent-py-gpt/tree/agent-main/app/agent): LLMs utils, including the different agents. 
- [Prompts](https://github.com/jimysancho/agent-py-gpt/tree/agent-main/app/prompts): The prompts used to "train" the agents and to answer the queries. 

# 4. How to use it? 

1. You'll need llama3 running
2. In the terminal: ```uvicorn app.main:app --reload --host 0.0.0.0 --port 3000``` (it is not include in the docker because of incompatibities with rag-pychunk) 
3. docker compose up -d 
4. Go to: ```localhost:8501``` and upload your python code in a zip file. 
5. Start chatting with your repository!


# Comments

When you update your code, all the files will be saved on a folder called user_code inside the folder of this cloned repository. The files will be saved according to your zip file (the operation is just an unzip function). 

**If you want to update your code, you don't need to make changes and upload the zip file again! Just make the changes inside the user_code folder, save them and click on the `Update your database` button!**. 

The changed files will be rewritten in your database and new relationships will be computed! 

Env example: 

```
export DB_USER='<user>'
export DB_PASSWORD='<password>'
export DB_NAME='<db-name>'
export USER_CODE_DIRECTORY='./user_code'
export FILES_STRUCTURE_FOLDER='./files_structure'
export NAMES_FILE='./name.txt'
export RELATIONSHIPS_FILE='./node_relationships.txt'
export THRESHOLD='0.25'
```

# Problems

#### 1. pgvector on docker
If for some reason you can't install pgvector on the docker image for postgres, remove the part of pgvector and create it manually. 

```
FROM postgres:16-alpine

RUN apk update && apk add --no-cache \
    build-base \
    postgresql-dev \
    wget \
    unzip \
    git
```

Then follow the instructions of pgvector to create the extension on the database you wanted. 