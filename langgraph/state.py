from typing import Annotated
from typing import TypedDict, Sequence
from langgraph.graph import add_messages
from langchain_core.messages import BaseMessage
from operator import add


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]  # Chat messages
    steps: Annotated[list[str], add]  # Agent steps
    question: str  # Query executed against the database to retrieve documents
    documents: list[str]  # Retrieved documents (context)
    reranked_documents: list[str]
    prompt: str  # Prompt used for generation
    generation: str  # Generated text
    answer: str  # Generated final answer
    queries: list[str]  # Queries used to retrieve documents
    context: str  # Context to use to answer the question. It is a subset of all documents, trimmed to only what is relevant
    sources: list[str]
