CHOOSE_RETRIEVER = """
You are going to receive a python related question. This question can belong to one of 3 categories: general, particular, complex. Classify the question according to :\n
1. Particular: the user will ask about features of one function, class or block of code. \n
2. General: the user will ask about a feature of some component but in a general context. \n
3. Complex: the user will ask about features of specific components but that involve at least two different components: class, functions, methods or blocks of code. \n
Think about it. \n
Your output must follow this format: 
{"question_type": <Question Type>, "reasoning": reasoning}
------- EXAMPLES -------
Python question: are there any errors in this repository? \n
Reasoning: The user is asking about errors in the hole repository, so the answer is general since there is nothing specific. \n
Question type: general \n
Output: {"question_type": "general", "reasoning": "The user is asking about erros in the hole repository, so the answer is general since there is nothing specific"} \n

Python question: what does the function <function name> do? \n
Reasoning: The user is asking about a particular function, so the answer is particular. \n
Question type: particular \n
Output: {"question_type": "particular", "reasoning": "The user is asking about a particular function, so the answer is particular"} \n

Python question: what would happen if I change the arguments in the function X? \n
Reasoning: The user is asking about the effects that his change will have in general, so the answer is general. \n
Question type: general \n
Output: {"question_type": "general", "reasoning": "The user is asking about the effects that his change will have in general, so the answer is general"} \n

Python question: How does the function function_1 affect the return of the function function_2? \n
Reasoning: The user is asking about two functions, so the answer is complex because there is more than one element is involved. \n
Question type: complex \n
Output: {"question_type": "complex", "reasoning": "The user is asking about how two functions are related and how one of them affects the other, so the answer is complex because more than one element is involved"} \n

Python question: Where is the function function_x called inside the repository? \n
Reasoning: The user is asking about a particular function but the context is the hole repository, so the answer is general. \n
Question type: general \n
Output: {"question_type": "general", "reasoning": "The user is asking about a particular function but the context is ther repository, so the answer is general"} \n

------ END EXAMPLES --------
Python question: {query}
Output: 
"""

SIMPLE_VS_COMPLEX = """
Based on this question: {query} classify it into two categories: [complex, simple] based on this: \n
- Complex: more than one subject is involved in the question. \n
- Simple: one or zero subject is involded in the question. \n
Important: do not assume anything. Identify the subjects only from the question. A subject can be: a function, a class, a method or a block of code. It must be explicit in the question to be a subject. If not, there is no subject. 
These are not subjects: Arguments of functions, arguments of methods or arguments of classes, repository, files, folders are not subjects neither.\n
\n
Your output must follow this JSON format without saying anything else: 
\n
{"question_type": <question_type>, "subject": <subject(s)>, "reasoning": <your reasoning>}
\n
---------------- EXAMPLES --------------------
Question: "How does the function X work?" \n
Output: \n
{"question_type": "simple", "subject": ["X"], "reasoning": "The subject is function X therefore the answer is particular since there is only one subject"} \n

Question: "If I change the argument of the function f, wil that affect the rest of my code?", \n
Output: \n
{"question_type": "simple", "subject": ["f"], "reasoning": "The subject is the function f therefore the answer is simple because there is one subject "}\n
 
Question: "If i change the parameter alpha of the method _create_of_nodes, how will that affect the class Node?", 
Output: \n
{"question_type": "complex", "subject": ["_create_of_nodes", "Node"], "reasoning": "The subjects are: _create_of_nodes function and Node class, therefore the answer is complex because there is more than one subject."}

Question: "Is there any file called main.py?"
Output: \n
{"question_type": "simple", "subject": [None], "reasoning": "main.py file is a file therefore is no subject and therefore there are no subjects, so the question is simple since there are no subjects. "}

---------------- END EXAMPLES --------------------
Again, this is the question: {query}
Output: \n
"""

GENERAL_VS_PARTICULAR_CONTEXT = """
Classify the question down below in one of two categories: [particular, complex] according to the following criteria: 
- particular: the question refer only to the subject. 
- general: the question does not refer only to the subject or it refers to the subject in a general way.
--------- EXAMPLES ----------

Question: "How does the function X work?" \n
Output: \n
{"question_type": "particular", "subject": ["X"], "reasoning": "The question is regarding function X itself, therefore the answer is particular"} \n

Question: "If I change the argument of the function f, will that affect the rest of my code?", \n
Output: \n
{"question_type": "general", "subject": ["f"], "reasoning": "The question is about the rest of the code, which is not about the subject, therefore the answer is general."}\n
 
Question: "If i change the parameter alpha of the method _create_of_nodes, how will that affect the repository", 
Output: \n
{"question_type": "general", "subjects": ["_create_of_nodes"], "reasoning": "The question involves the repository, which is different than the subject, therefore the answer is general."}

Question: "Where is the class Dog called?"
Output: \n
{"question_type": "general", "subjects": ["Dog"], "reasoning": "The question referes to the subject in a very general way, therefore the answer is general"}

-------- END EXAMPLES --------

Your output must follow the next schema without saying anything else: 
{"subject": <provided subjects>, "question_type": <particular or general>, "reasoning": <your reasoning>}

Question: {query}
Subjects: {subject}
Output: \n
"""