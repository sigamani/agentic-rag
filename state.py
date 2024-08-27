from typing import Annotated
import json
import re
from typing import TypedDict, Annotated, Sequence
from langgraph.graph import add_messages
from langchain_core.messages import BaseMessage
from operator import add


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]  # Chat messages
    steps: Annotated[list[str], add]  # Agent steps
    question: str  # Query executed against the database to retrieve documents
    documents: list[str]  # Retrieved documents (context)
    prompt: str  # Prompt used for generation
    generation: str  # Generated text
    answer: str  # Generated final answer
