import os

CHAT_MODEL = "mistral"
EMBED_MODEL = "nomic-embed-text"
TOKEN_LENGTH = 500

DATA_DIR = "data"
PDF_FILE = os.path.join(DATA_DIR, "whirlpool.pdf")
TEXT_FILE = os.path.join(DATA_DIR, "whirlpool.txt")
CHROMA_DB_DIR = os.path.join(DATA_DIR, "chroma_db")
BENCHMARK_FILE = os.path.join(DATA_DIR, "benchmark_unified.json")

COLLECTION_NAME = "semantic-chunks"
CHUNK_STRATEGIES = ["semantic", "agentic", "title", "hybrid", "graph_based"]
