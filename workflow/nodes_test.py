"""
Test version of workflow nodes using mock dependencies for end-to-end testing.
"""
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

# Use mock dependencies for testing
from data.retrieve_stub import MockRelevantDocumentRetriever, vector_store
from models.llm_stub import llm, MODEL_NAME

import dotenv
from utils.utils import format_prompt
from concurrent.futures import ThreadPoolExecutor, as_completed

dotenv.load_dotenv()

cheating_retriever = MockRelevantDocumentRetriever(DATA_PATH)

def extract_question(state: dict) -> dict:
    question = (
        state.get("question")
        or state.get("Question")
        or (state.get("messages")[-1].content if state.get("messages") else "")
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
    queries = state.get("queries", [state["question"]])  # Default to question if no queries

    results = []
    unique_docs = {}

    # Function to search and return results for a query
    def search_query(query):
        return vector_store.similarity_search(
            query, k=config.retrieval_k
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
    question = state.get("question", "")
    
    prompt = generate_queries_prompt_template.format(question=question)
    response = llm.invoke(prompt)
    
    # Parse the mock response into a list of queries
    queries = [q.strip() for q in response.split('\n') if q.strip() and not q.strip().startswith('Question:')]
    queries = [q.lstrip('1234567890.- ') for q in queries if q.lstrip('1234567890.- ')]
    
    return {"queries": queries[:3]}  # Limit to 3 queries

def rerank(state: AgentState, config: GraphConfig) -> AgentState:
    if CHEATING_RETRIEVAL:
        return {
            "reranked_documents": state["documents"],
            "context": format_docs(state["documents"]),
        }

    # Mock reranking - just return top documents
    reranked_docs = state["documents"][:config.rerank_k]
    return {"reranked_documents": reranked_docs, "context": format_docs(reranked_docs)}

def format_docs(docs: list[Document]) -> str:
    formatted = ""
    for doc in docs:
        formatted += f"<DOC ID={doc.metadata['id']}>\n{doc.page_content}\n</DOC>\n\n"
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
        response = llm.invoke(prompt)
        response_message = AIMessage(response)

    return {
        "prompt": prompt,
        "generation": response_message,
    }

def extract_answer(state: AgentState) -> AgentState:
    if DISABLE_GENERATION:
        return {"answer": "NO ANSWER"}

    generation = state["generation"]
    if hasattr(generation, "content"):
        generation = generation.content

    match = re.search(r"<ANSWER>(.*?)</ANSWER>", generation, re.DOTALL)
    extracted_answer = match.group(1).strip() if match else ""

    # Sometimes, the <ANSWER> tags are missing/corrupted even though the answer is written
    # In these cases, we can use LLM to extract the answer
    if not extracted_answer:
        prompt = extract_anwer_prompt_template.format(
            question=state["question"], generation=generation
        )
        print(f"Extracting answer using LLM... {prompt}")
        extracted_answer = llm.invoke(prompt)
        extracted_answer = extracted_answer.replace("<OUTPUT>", "").replace("</OUTPUT>", "")
        extracted_answer = extracted_answer.replace("<ANSWER>", "").replace("</ANSWER>", "")
    
    return {"answer": extracted_answer}