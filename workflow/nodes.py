import os
import re
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.documents import Document
from config import DATA_PATH, CHEATING_RETRIEVAL, DISABLE_GENERATION, GraphConfig
from utils.prompts import (
    reason_and_answer_prompt_template,
    extract_anwer_prompt_template,
    filter_context_prompt_template,
    generate_queries_prompt_template,
)
from .state import AgentState

from data.retrieve import RelevantDocumentRetriever, vector_store
from models.llm import llm, MODEL_NAME

import dotenv

from utils import format_prompt
import cohere
from concurrent.futures import ThreadPoolExecutor, as_completed


dotenv.load_dotenv()

cheating_retriever = RelevantDocumentRetriever(DATA_PATH)


def extract_question(state: dict) -> dict:
    question = (
        state.get("question")
        or state.get("Question")
        or (state.get("messages")[-1] if state.get("messages") else "")
    )
    return {"question": question.strip()}


def extract_answer(state: dict) -> dict:
    generation = state.get("generation")

    if hasattr(generation, "content"):
        generation = generation.content  # ✅ unwrap AIMessage

    match = re.search(r"<ANSWER>(.*?)</ANSWER>", generation or "", re.DOTALL)
    if match:
        answer = match.group(1).strip()
    else:
        answer = generation or ""

    return {"answer": answer}




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
    context = "\n\n".join([doc.page_content for doc in results])
    return {
        "documents": results,
        "context": context
    }

def generate_queries(state: dict) -> dict:
    context = state.get("context", "")
    question = state.get("question", "")

    prompt = f"Context:\n{context}\n\nQuestion:\n{question}\nAnswer:"
    response = llm.invoke(prompt)
    return {"answer": response}


def filter_context(state: AgentState, config: GraphConfig) -> AgentState:
    question = state["question"]
    documents = state["reranked_documents"]

    prompt = filter_context_prompt_template.format(
        question=question, documents=format_docs(documents)
    )
    response = llm.invoke(
        input=prompt,
        #model=MODEL_NAME,
        #max_tokens=config["configurable"].get("max_tokens", 4096),
       # temperature=0,
    )
    response_text = response.replace("<OUTPUT>", "").replace("</OUTPUT>", "")

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
           # model=MODEL_NAME,
            input=prompt,
          #  max_tokens=config["configurable"].get("max_tokens", 4096),
          #  temperature=config["configurable"].get("temperature", 0.0),
          #  top_p=config["configurable"].get("top_p", 0.9),
        )
        response_message = AIMessage(response)

    return {
        "prompt": prompt,
        "generation": response_message,
    }


# generate_chat function removed - unused in current LangGraph workflow


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
            #model=MODEL_NAME, input=format_prompt(prompt), max_tokens=100
           input=prompt
        ).content
        extracted_answer = extracted_answer.replace("<OUTPUT>", "").replace(
            "</OUTPUT>", ""
        )
        extracted_answer = extracted_answer.replace("<ANSWER>", "").replace(
            "</ANSWER>", ""
        )
    return {"answer": extracted_answer}
