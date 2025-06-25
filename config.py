"""Configuration settings for the financial RAG assistant."""

from pydantic import BaseModel, Field
import os

# Data and retrieval settings
DATA_PATH = os.getenv("DATA_PATH", "./data")
CHEATING_RETRIEVAL = os.getenv("CHEATING_RETRIEVAL", "false").lower() == "true"
DISABLE_GENERATION = os.getenv("DISABLE_GENERATION", "false").lower() == "true"

# HuggingFace Cache Settings (optimized for cloud storage)
HF_HOME = os.getenv("HF_HOME", os.path.expanduser("~/hf-cache-optimized"))
HF_HUB_CACHE = os.getenv("HF_HUB_CACHE", os.path.join(HF_HOME, "hub"))
HF_DATASETS_CACHE = os.getenv("HF_DATASETS_CACHE", os.path.join(HF_HOME, "datasets"))
TRANSFORMERS_CACHE = os.getenv("TRANSFORMERS_CACHE", os.path.join(HF_HOME, "transformers"))

class GraphConfig(BaseModel):
    """Pydantic v2 configuration schema for the LangGraph workflow."""
    
    retrieval_k: int = Field(
        default=5,
        description="Number of documents to retrieve",
        ge=1, le=20
    )
    rerank_k: int = Field(
        default=3,
        description="Number of documents to rerank",
        ge=1, le=10
    )
    max_tokens: int = Field(
        default=4096,
        description="Maximum tokens for generation",
        ge=100, le=8192
    )
    temperature: float = Field(
        default=0.0,
        description="Temperature for generation",
        ge=0.0, le=2.0
    )
    top_p: float = Field(
        default=0.9,
        description="Top-p for generation",
        ge=0.0, le=1.0
    )

# Default configuration values
DEFAULT_CONFIG = GraphConfig()