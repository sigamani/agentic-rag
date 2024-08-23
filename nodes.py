import re
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.documents import Document
from config import DATA_PATH
from prompts import prompt_template

from state import AgentState

from retrieve import RelevantDocumentRetriever
from llm import llm


cheating_retriever = RelevantDocumentRetriever(DATA_PATH)

    
def extract_question(state: AgentState) -> AgentState:
    messages = state["messages"]
    question = messages[-1].content
    return {"question": question, "steps": ["extract_question"]}

def retrieve_relevant_only(state: AgentState) -> AgentState:
    question = state['question']
    return {"documents": [cheating_retriever.query(question)]}

# Post-processing
def format_docs(docs: list[Document]):
    return "\n\n".join(doc.page_content for doc in docs)

def generate(state: AgentState) -> AgentState:
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

    response = llm.chat.completions.create(model="llama3.1", messages=messages_openai)
    response_message = AIMessage(response.choices[0].message.content)
    return {"messages": [response_message], "prompt": messages_openai, "generation": response_message.content}

def extract_answer(state: AgentState) -> AgentState:
    last_message = state["messages"][-1].content

    match = re.search(r'<ANSWER>(.*?)</ANSWER>', last_message, re.DOTALL)
    extracted_answer = match.group(1).strip() if match else ""

    return {"answer": extracted_answer}