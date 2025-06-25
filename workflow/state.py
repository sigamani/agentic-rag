from typing import Annotated, Sequence, Optional, List
from pydantic import BaseModel, Field
from langgraph.graph import add_messages
from langchain_core.messages import BaseMessage
from langchain_core.documents import Document
from operator import add


class AgentState(BaseModel):
    """Pydantic v2 model for the financial RAG workflow state."""
    
    messages: Annotated[Sequence[BaseMessage], add_messages] = Field(
        default_factory=list, 
        description="Chat messages in the conversation"
    )
    steps: Annotated[List[str], add] = Field(
        default_factory=list,
        description="Agent processing steps"
    )
    question: str = Field(
        default="",
        description="User question to be answered"
    )
    documents: List[Document] = Field(
        default_factory=list,
        description="Retrieved documents for context"
    )
    reranked_documents: List[Document] = Field(
        default_factory=list,
        description="Reranked documents after relevance scoring"
    )
    prompt: str = Field(
        default="",
        description="Generated prompt for the LLM"
    )
    generation: str = Field(
        default="",
        description="LLM generated response"
    )
    answer: str = Field(
        default="",
        description="Final extracted answer"
    )
    queries: List[str] = Field(
        default_factory=list,
        description="Search queries for document retrieval"
    )
    context: str = Field(
        default="",
        description="Filtered context from relevant documents"
    )
    sources: List[str] = Field(
        default_factory=list,
        description="Source document IDs used in the answer"
    )
    
    class Config:
        """Pydantic v2 configuration."""
        arbitrary_types_allowed = True
