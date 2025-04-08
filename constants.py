import os

CHAT_MODEL = "deepseek-r1:8b"
EMBED_MODEL = "all-minilm"
TOKEN_LENGTH = 500

DATA_DIR = "data"
PDF_FILE = os.path.join(DATA_DIR, "whirlpool.pdf")
TEXT_FILE = os.path.join(DATA_DIR, "whirlpool.txt")
CHROMA_DB_DIR = os.path.join(DATA_DIR, "chroma_db")
BENCHMARK_FILE = os.path.join(DATA_DIR, "benchmark_unified.json")

COLLECTION_NAME = "semantic-chunks"
CHUNK_STRATEGIES = ["semantic", "agentic", "title", "hybrid", "graph_based"]
