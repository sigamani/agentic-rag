from datetime import datetime
import os
import re
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.documents import Document
from config import DATA_PATH
from prompts import reason_and_answer_prompt_template, extract_anwer_prompt_template
from state import AgentState

from retrieve import RelevantDocumentRetriever, vector_store
from llm import llm, MODEL_NAME
from langfuse.decorators import observe

import dotenv

from utils import format_prompt

dotenv.load_dotenv()

cheating_retriever = RelevantDocumentRetriever(DATA_PATH)
CHEATING_RETRIEVAL = True
DISABLE_GENERATION = False
MAX_TOKENS = 4096


@observe()
def extract_question(state: AgentState) -> AgentState:
    messages = state["messages"]
    question = messages[-1].content
    return {"question": question, "steps": ["extract_question"]}


@observe()
def retrieve(state: AgentState) -> AgentState:
    if CHEATING_RETRIEVAL:
        return retrieve_relevant_only(state)
    else:
        return retrieve_from_vector_db(state)


@observe()
def retrieve_relevant_only(state: AgentState) -> AgentState:
    question = state["question"]
    return {"documents": cheating_retriever.query(question)}


@observe()
def retrieve_from_vector_db(state: AgentState) -> AgentState:
    question = state["question"]
    result = vector_store.similarity_search(question, k=5)

    return {
        "steps": [f"retrieve('{question}')"],
        "documents": result,
    }


@observe()
def rerank(state: AgentState) -> AgentState:
    question = state["question"]
    documents = state["documents"]

    # TODO: rerank

    return {"steps": ["rerank"]}


# Post-processing
def format_docs(docs: list[Document]):
    return "\n\n".join(doc.page_content for doc in docs)


@observe()
def generate(state: AgentState) -> AgentState:
    question = state["question"]
    documents = state["documents"]

    prompt = reason_and_answer_prompt_template.format(
        **{"question": question, "documents": format_docs(documents)}
    )

    if DISABLE_GENERATION:
        # This is useful for retrieval development
        response_message = AIMessage("[GENERATION DISABLED]")
    else:
        response = llm.completions.create(
            model=MODEL_NAME,
            prompt=format_prompt(prompt),
            max_tokens=MAX_TOKENS,
            temperature=0,
            top_p=0.5,
        )
        response_message = AIMessage(response.choices[0].text)

    return {
        "messages": [response_message],
        "prompt": prompt,
        "generation": response_message.content,
    }


@observe()
def generate_chat(state: AgentState) -> AgentState:
    messages = state["messages"]
    question = state["question"]
    documents = state["documents"]

    prompt = reason_and_answer_prompt_template.format(
        **{"question": question, "documents": format_docs(documents)}
    )
    messages[-1] = HumanMessage(prompt)

    messages_openai = []
    for message in messages:
        if isinstance(message, HumanMessage):
            role = "user"
        elif isinstance(message, AIMessage):
            role = ("assistant",)
        else:
            raise ValueError("No such message type allowed")
        messages_openai.append(({"role": role, "content": message.content}))

    response = llm.chat.completions.create(model=MODEL_NAME, messages=messages_openai)
    response_message = AIMessage(response.choices[0].message.content)
    return {
        "messages": [response_message],
        "prompt": messages_openai,
        "generation": response_message.content,
    }


@observe()
def extract_answer(state: AgentState) -> AgentState:
    last_message = state["messages"][-1].content

    match = re.search(r"<ANSWER>(.*?)</ANSWER>", last_message, re.DOTALL)
    extracted_answer = match.group(1).strip() if match else ""

    # Sometimes, the <ANSWER> tags are missing/corrupted even though the answer is written
    # In these cases, we can use LLM to extract the answer
    if not extracted_answer:
        prompt = extract_anwer_prompt_template.format_prompt(
            **{"question": state["question"], "generation": state["generation"]}
        )
        extracted_answer = (
            llm.completions.create(
                model=MODEL_NAME, prompt=format_prompt(prompt), max_tokens=100
            )
            .choices[0]
            .text
        )
        extracted_answer = extracted_answer.replace("<OUTPUT>", "").replace(
            "</OUTPUT>", ""
        )
        extracted_answer = extracted_answer.replace("<ANSWER>", "").replace(
            "</ANSWER>", ""
        )
    return {"answer": extracted_answer}
