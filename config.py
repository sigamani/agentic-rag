from typing import TypedDict

DATA_PATH = "ConvFinQA/data/train.json"
DATA_LIMIT_EVAL = 1000
DATA_LIMIT_DB = 10000
CHEATING_RETRIEVAL = False
DISABLE_GENERATION = False
LANGFUSE_DATASET_NAME = "convfinqa-train"
COLLECTION_NAME = "financial_docs"
EMBEDDING_MODEL = "multi-qa-mpnet-base-dot-v1"
DB_PATH = "./vector_database"

class GraphConfig(TypedDict):
    retrieval_k: int = 10
    rerank_k: int = 3
    max_tokens: int = 4096
    temperature: float = 0.0