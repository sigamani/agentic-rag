from collections import defaultdict
from utils import format_document

import json
import chromadb
from chromadb.utils import embedding_functions
from langchain_chroma import Chroma
from sentence_transformers import SentenceTransformer
from langchain_core.documents import Document

COLLECTION_NAME = "financial_docs"
EMBEDDING_MODEL = "multi-qa-mpnet-base-dot-v1"


# Langchain compatible embeddings
class CustomEmbeddings:
    def __init__(self, model="all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model, trust_remote_code=True)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self.model.encode(t).tolist() for t in texts]

    def embed_query(self, query: str) -> list[float]:
        return self.model.encode([query])[0].tolist()


DB_PATH = "./vector_database"

# ChromaDB setup
sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name=EMBEDDING_MODEL
)
chromadb_client = chromadb.PersistentClient(path=DB_PATH)
db = chromadb_client.get_or_create_collection(
    name=COLLECTION_NAME, embedding_function=sentence_transformer_ef
)

# Langchain Setup
vector_store = Chroma(
    client=chromadb_client,
    collection_name=COLLECTION_NAME,
    persist_directory=DB_PATH,  # Where to save data locally, remove if not neccesary
    embedding_function=CustomEmbeddings(EMBEDDING_MODEL),
)


class RelevantDocumentRetriever:
    def _create_question_to_document_map(
        self, filepath: str, limit: int = None
    ) -> dict[str, list[Document]]:
        q2d = defaultdict(list)

        with open(filepath, "r") as f:
            data = json.load(f)

        QA_FIELDS = ["qa", *[f"qa_{i}" for i in range(10)]]
        if limit:
            data = data[:limit]

        for entry in data:
            # Loop through every available QA field in the entry
            for qa_field in set(QA_FIELDS).intersection(entry.keys()):
                q2d[entry[qa_field]["question"]].append(format_document(entry))

        return q2d

    def __init__(self, data_path: str, limit: int = None):
        self.q2d = self._create_question_to_document_map(data_path, limit=limit)

    def __call__(self, question):
        return self.q2d[question]

    def query(self, question):
        return self.q2d[question]
