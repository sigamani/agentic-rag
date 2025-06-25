"""Configuration settings for the financial RAG assistant."""

from typing import TypedDict
import os

# Data and retrieval settings
DATA_PATH = os.getenv("DATA_PATH", "./data")
CHEATING_RETRIEVAL = os.getenv("CHEATING_RETRIEVAL", "false").lower() == "true"
DISABLE_GENERATION = os.getenv("DISABLE_GENERATION", "false").lower() == "true"

class GraphConfig(TypedDict):
    """Configuration schema for the LangGraph workflow."""
    retrieval_k: int  # Number of documents to retrieve
    rerank_k: int     # Number of documents to rerank
    max_tokens: int   # Maximum tokens for generation
    temperature: float # Temperature for generation
    top_p: float      # Top-p for generation

# Default configuration values
DEFAULT_CONFIG = GraphConfig(
    retrieval_k=5,
    rerank_k=3,
    max_tokens=4096,
    temperature=0.0,
    top_p=0.9
)