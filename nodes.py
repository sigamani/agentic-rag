import os
import re
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.documents import Document
from config import DATA_PATH
from prompts import prompt_template

from state import AgentState

from retrieve import RelevantDocumentRetriever, vector_store
from llm import llm, MODEL_NAME

import dotenv
dotenv.load_dotenv()

cheating_retriever = RelevantDocumentRetriever(DATA_PATH)
CHEATING_RETRIEVAL = False
DISABLE_GENERATION = True

def extract_question(state: AgentState) -> AgentState:
    messages = state["messages"]
    question = messages[-1].content
    return {"question": question, "steps": ["extract_question"]}

def retrieve(state: AgentState) -> AgentState:
    if CHEATING_RETRIEVAL:
        return retrieve_relevant_only(state)
    else:
        return retrieve_from_vector_db(state)

def retrieve_relevant_only(state: AgentState) -> AgentState:
    question = state['question']
    return {"documents": cheating_retriever.query(question)}

def retrieve_from_vector_db(state: AgentState) -> AgentState:
    question = state["question"]
    result = vector_store.similarity_search(question, k=5)
    
    return {
        "steps": [f"retrieve('{question}')"], 
        "documents": result, 
    }

# Post-processing
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)
    
def rerank(state: AgentState) -> AgentState:
    question = state["question"]
    documents = state["documents"]

    # TODO: rerank

    return {"steps": ["rerank"]}

# Post-processing
def format_docs(docs: list[Document]):
    return "\n\n".join(doc.page_content for doc in docs)

def generate(state: AgentState) -> AgentState:
    question = state["question"]
    documents = state["documents"]

    prompt = prompt_template.format(**{"question": question, "documents": format_docs(documents)})

    if DISABLE_GENERATION:
        # This is useful for retrieval development
        response_message = AIMessage("[GENERATION DISABLED]")
    else:
        response = llm.completions.create(model=MODEL_NAME, prompt=prompt)
        response_message = AIMessage(response.choices[0].text)
    return {"messages": [response_message], "prompt": prompt, "generation": response_message.content}

def generate_chat(state: AgentState) -> AgentState:
    messages = state["messages"]
    question = state["question"]
    documents = state["documents"]

    prompt = prompt_template.format(**{"question": question, "documents": format_docs(documents)})
    messages[-1] = HumanMessage(prompt)
    
    messages_openai = []
    for message in messages:
        if isinstance(message, HumanMessage):
            role = "user"
        elif isinstance(message, AIMessage):
            role = "assistant",
        else:
            raise ValueError("No such message type allowed")
        messages_openai.append(({"role": role, "content": message.content}))

    response = llm.chat.completions.create(model=MODEL_NAME, messages=messages_openai)
    response_message = AIMessage(response.choices[0].message.content)
    return {"messages": [response_message], "prompt": messages_openai, "generation": response_message.content}

def extract_answer(state: AgentState) -> AgentState:
    last_message = state["messages"][-1].content

    match = re.search(r'<ANSWER>(.*?)</ANSWER>', last_message, re.DOTALL)
    extracted_answer = match.group(1).strip() if match else ""

    return {"answer": extracted_answer}