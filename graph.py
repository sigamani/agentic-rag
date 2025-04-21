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

from langsmith.run_helpers import traceable
from utils import typed_dict_to_dict

dotenv.load_dotenv()


def answer_exists(state: AgentState) -> AgentState:
    return state["answer"]


# Workflow
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
    from IPython.display import Image
    from langchain_core.runnables.graph import MermaidDrawMethod
    inputs = {
        "messages": [
            HumanMessage(
                "what was the percentage change in the net cash from operating activities from 2008 to 2009"
            ),
        ]
    }

    for output in graph.stream(inputs, config={"callbacks": [langfuse_handler],
                                               "configurable":
                                                   typed_dict_to_dict(GraphConfig)
                                               }):
        for key, value in output.items():
            print(f"Output from node '{key}':")
            print("---")
            pprint.pprint(value, indent=2, width=80, depth=None)
        print()
        print("---")
        print()



    image_bytes = graph.get_graph().draw_mermaid_png(
        draw_method=MermaidDrawMethod.API,
    )

    # Save the image to a file
    with open("graph.png", "wb") as f:
        f.write(image_bytes)

    # Open the saved image
    image = Image.open("graph.png")
