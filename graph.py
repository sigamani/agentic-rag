from langgraph.graph import StateGraph
from langchain_core.messages import HumanMessage
import dotenv
from config import GraphConfig

from nodes import (
    extract_question,
    generate,
    extract_answer,
    retrieve,
    rerank,
    generate_queries,
)
from state import AgentState

from langfuse_config import langfuse_handler

dotenv.load_dotenv()


def answer_exists(state: AgentState) -> AgentState:
    return state["answer"]


workflow = StateGraph(AgentState, config_schema=GraphConfig)

# Nodes
workflow.add_node("extract_question", extract_question)
workflow.add_node("generate_queries", generate_queries)
workflow.add_node("retriever", retrieve)
workflow.add_node("reranker", rerank)
workflow.add_node("generator", generate)
workflow.add_node("extract_answer", extract_answer)

# Edges
workflow.set_entry_point("extract_question")

workflow.add_edge("extract_question", "generate_queries")
workflow.add_edge("generate_queries", "retriever")
workflow.add_edge("retriever", "reranker")
workflow.add_edge("reranker", "generator")
workflow.add_edge("generator", "extract_answer")

workflow.set_finish_point("extract_answer")

graph = workflow.compile()


if __name__ == "__main__":
    import pprint

    inputs = {
        "messages": [
            HumanMessage(
                "what was the percentage change in the net cash from operating activities from 2008 to 2009"
            ),
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
