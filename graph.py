import json
import re
from typing import Literal, TypedDict, Annotated, Sequence
from langchain_chroma import Chroma
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage
from langchain.prompts import PromptTemplate
from operator import add

from nodes import extract_question, retrieve_relevant_only, generate, extract_answer, retrieve_from_vector_db, rerank
from state import AgentState

from langfuse_config import langfuse, langfuse_handler

CHEATING_RETRIEVAL = True

# Ollama
from openai import OpenAI

openai_api_key = "YOUR_API_KEY"
openai_api_base = "http://localhost:11434/v1"

llm = OpenAI(api_key=openai_api_key, base_url=openai_api_base)

class GraphConfig(TypedDict):
    retrieval_k: int = 5

def answer_exists(state: AgentState) -> AgentState:
    return state['answer']

workflow = StateGraph(AgentState, config_schema=GraphConfig)
if CHEATING_RETRIEVAL:
    workflow.add_node("extract_question", extract_question)
    workflow.add_node("cheating_retriever", retrieve_relevant_only)
    workflow.add_node("generator", generate)
    workflow.add_node("extract_answer", extract_answer)

    workflow.add_edge("extract_question", "cheating_retriever")
    workflow.add_edge("cheating_retriever", "generator")
    workflow.add_edge("generator", "extract_answer")
    # workflow.add_conditional_edges("extract_answer", answer_exists, {True: END, False: "generator"})
else:
    workflow.add_node("extract_question", extract_question)
    workflow.add_node("retriever", retrieve_from_vector_db)
    workflow.add_node("reranker", rerank)
    workflow.add_node("generator", generate)
    workflow.add_node("extract_answer", extract_answer)

    workflow.add_edge("extract_question", "retriever")
    workflow.add_edge("retriever", "reranker")
    workflow.add_edge("reranker", "generator")
    workflow.add_edge("generator", "extract_answer")
    # workflow.add_conditional_edges("extract_answer", answer_exists, {True: END, False: "generator"})

workflow.set_entry_point("extract_question")
workflow.set_finish_point("extract_answer")
graph = workflow.compile()


if __name__ == "__main__":
    import pprint    

    inputs = {
        "messages": [
            HumanMessage('what was the percentage change in the net cash from operating activities from 2008 to 2009'),
        ]
    }

    for output in graph.stream(inputs, config={"callbacks": [langfuse_handler]}):
        for key, value in output.items():
            print(f"Output from node '{key}':")
            print("---")
            pprint.pprint(value, indent=2, width=80, depth=None)
        print()
        print("---")
        print()