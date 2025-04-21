import os
import re
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.documents import Document
from config import DATA_PATH, CHEATING_RETRIEVAL, DISABLE_GENERATION, GraphConfig
from prompts import (
    reason_and_answer_prompt_template,
    extract_anwer_prompt_template,
    filter_context_prompt_template,
    generate_queries_prompt_template,
)
from state import AgentState

from retrieve import RelevantDocumentRetriever, vector_store
from llm import llm, MODEL_NAME

import dotenv

from utils import format_prompt
import cohere
from concurrent.futures import ThreadPoolExecutor, as_completed


dotenv.load_dotenv()

cheating_retriever = RelevantDocumentRetriever(DATA_PATH)


def extract_question(state: AgentState, config: GraphConfig) -> AgentState:
    messages = state["messages"]
    question = messages[-1].content
    return {"question": question}


def retrieve(state: AgentState, config: GraphConfig) -> AgentState:
    if CHEATING_RETRIEVAL:
        return retrieve_relevant_only(state)
    else:
        return retrieve_from_vector_db(state, config)


def retrieve_relevant_only(state: AgentState) -> AgentState:
    question = state["question"]
    return {"documents": cheating_retriever.query(question)}


def retrieve_from_vector_db(state: AgentState, config: GraphConfig) -> AgentState:
    queries = state["queries"]

    results = []
    unique_docs = {}

    # Function to search and return results for a query
    def search_query(query):
        return vector_store.similarity_search(
            query, k=config["configurable"].get("retrieval_k", 5)
        )

    # Parallelize the search across queries
    with ThreadPoolExecutor() as executor:
        future_to_query = {
            executor.submit(search_query, query): query for query in queries
        }

        for future in as_completed(future_to_query):
            search_results = future.result()
            for doc in search_results:
                doc_id = doc.metadata["id"]
                if doc_id not in unique_docs:
                    unique_docs[doc_id] = doc

    results = list(unique_docs.values())

    return {
        "documents": results,
    }


def generate_queries(state: AgentState, config: GraphConfig) -> AgentState:
    question = state["question"]
    prompt = generate_queries_prompt_template.format(question=question)
    response = llm.invoke(
        input=format_prompt(prompt),
        model=MODEL_NAME,
        max_tokens=config["configurable"].get("max_tokens", 4096),
        temperature=0,
    )

    queries = response.content.split("\n")
    queries.append(question)  # add original question

    return {
        "queries": queries,
    }


def filter_context(state: AgentState, config: GraphConfig) -> AgentState:
    question = state["question"]
    documents = state["reranked_documents"]

    prompt = filter_context_prompt_template.format(
        question=question, documents=format_docs(documents)
    )
    response = llm.invoke(
        input=format_prompt(prompt),
        model=MODEL_NAME,
        max_tokens=config["configurable"].get("max_tokens", 4096),
        temperature=0,
    )
    response_text = response.content.replace("<OUTPUT>", "").replace("</OUTPUT>", "")

    try:
        context, sources = re.split(
            "sources:", response_text, flags=re.IGNORECASE, maxsplit=1
        )
        context = context.strip()
        sources = [
            source.strip().lstrip("-").lstrip()
            for source in re.split("sources:", response_text, flags=re.IGNORECASE)[
                1
            ].split("\n")
        ]
        if "" in sources:
            sources.remove("")
    except IndexError:
        # when there are no sources provided (due to no information found or LLM error)
        sources = []

    return {"context": context, "sources": sources}


def rerank(state: AgentState, config: GraphConfig) -> AgentState:
    if CHEATING_RETRIEVAL:
        return {
            "reranked_documents": state["documents"],
            "context": format_docs(state["documents"]),
        }

    co = cohere.Client(os.getenv("COHERE_API_KEY"))

    docs = [
        {"text": doc.page_content, "id": doc.metadata["id"]}
        for doc in state["documents"]
    ]

    response = co.rerank(
        model="rerank-english-v3.0",
        query=state["question"],
        documents=docs,
        top_n=config["configurable"].get("rerank_k", 3),
    )

    reranked_docs = [state["documents"][result.index] for result in response.results]

    return {"reranked_documents": reranked_docs, "context": format_docs(reranked_docs)}


def format_docs(docs: list[Document]) -> str:
    formatted = ""
    for doc in docs:
        formatted += f"<DOC ID={doc.metadata['id']}>\n{doc.page_content}\n</DOC>"
    return formatted


def format_docs(docs: list[Document]) -> str:
    formatted = ""
    for doc in docs:
        formatted += f"<DOC ID={doc.metadata['id']}>\n{doc.page_content}\n</DOC>"
    return formatted


def generate(state: AgentState, config: GraphConfig) -> AgentState:
    question = state["question"]
    context = state["context"]

    prompt = reason_and_answer_prompt_template.format(
        **{"question": question, "context": context}
    )

    if DISABLE_GENERATION:
        # This is useful for retrieval development
        response_message = AIMessage("[GENERATION DISABLED]")
    else:
        response = llm.invoke(
            model=MODEL_NAME,
            input=format_prompt(prompt),
            max_tokens=config["configurable"].get("max_tokens", 4096),
            temperature=config["configurable"].get("temperature", 0.0),
            top_p=config["configurable"].get("top_p", 0.9),
        )
        response_message = AIMessage(response.content)

    return {
        "prompt": prompt,
        "generation": response_message.content,
    }


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

    response = llm.invoke(model=MODEL_NAME, input=messages_openai)
    response_message = AIMessage(response.content)
    return {
        "prompt": messages_openai,
        "generation": response_message.content,
    }


def extract_answer(state: AgentState) -> AgentState:
    if DISABLE_GENERATION:
        return {"answer": "NO ANSWER"}

    generation = state["generation"]
    match = re.search(r"<ANSWER>(.*?)</ANSWER>", generation, re.DOTALL)
    extracted_answer = match.group(1).strip() if match else ""

    # Sometimes, the <ANSWER> tags are missing/corrupted even though the answer is written
    # In these cases, we can use LLM to extract the answer
    if not extracted_answer:
        prompt = extract_anwer_prompt_template.format_prompt(
            **{"question": state["question"], "generation": generation}
        )
        print(f"Extracting answer using LLM... {prompt}")
        extracted_answer = llm.invoke(
            model=MODEL_NAME, input=format_prompt(prompt), max_tokens=100
        ).content
        extracted_answer = extracted_answer.replace("<OUTPUT>", "").replace(
            "</OUTPUT>", ""
        )
        extracted_answer = extracted_answer.replace("<ANSWER>", "").replace(
            "</ANSWER>", ""
        )
    return {"answer": extracted_answer}
