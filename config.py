from typing import TypedDict

DATA_PATH = "data/train.json"
DATA_LIMIT_EVAL = 10
DATA_LIMIT_DB = 10000
CHEATING_RETRIEVAL = False
DISABLE_GENERATION = False
COLLECTION_NAME = "financial_docs"
LANGFUSE_DATASET_NAME = "convfinqa-train2" 
EMBEDDING_MODEL = "multi-qa-mpnet-base-dot-v1"
DB_PATH = "./vector_database"

class GraphConfig(TypedDict):
    retrieval_k: int = 10
    rerank_k: int = 3
    max_tokens: int = 4096
    temperature: float = 0.0
