import re
import json
from collections import defaultdict

from config import COLLECTION_NAME, DB_PATH
from utils import format_document
import chromadb
from chromadb.utils import embedding_functions
from langchain_chroma import Chroma
from sentence_transformers import SentenceTransformer
from langchain_core.documents import Document

# LangChain-compatible embedding wrapper using BGE
class CustomEmbeddings:
    def __init__(self, model="BAAI/bge-base-en-v1.5"):
        self.model = SentenceTransformer(model, trust_remote_code=True)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self.model.encode(t).tolist() for t in texts]

    def embed_query(self, query: str) -> list[float]:
        return self.model.encode([query])[0].tolist()

# Create Chroma client and wrap as LangChain vector store
sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="BAAI/bge-base-en-v1.5"
)

chromadb_client = chromadb.PersistentClient(path=DB_PATH)

vector_store = Chroma(
    client=chromadb_client,
    collection_name=COLLECTION_NAME,
    persist_directory=DB_PATH,
    embedding_function=CustomEmbeddings("BAAI/bge-base-en-v1.5"),
)

# Helper to extract numbers from text
def extract_numbers(text: str) -> set:
    return set(re.findall(r"[-+]?[\\d]+(?:\\.\\d+)?[%$]?", text))

# Main retriever class
class RelevantDocumentRetriever:
    def _create_question_to_document_map(self, filepath: str, limit: int = None) -> dict[str, list[Document]]:
        q2d = defaultdict(list)
        with open(filepath, "r") as f:
            data = json.load(f)

        QA_FIELDS = ["qa", *[f"qa_{i}" for i in range(10)]]
        if limit:
            data = data[:limit]

        for entry in data:
            for qa_field in set(QA_FIELDS).intersection(entry.keys()):
                q2d[entry[qa_field]["question"]].append(format_document(entry))
        return q2d

    def __init__(self, data_path: str, limit: int = None):
        self.q2d = self._create_question_to_document_map(data_path, limit=limit)

    def __call__(self, question):
        return self.query(question)

    def query(self, question: str, top_k: int = 10, rerank_with_numeric: bool = True) -> list[Document]:
        docs = self.q2d.get(question, [])[:top_k]

        if rerank_with_numeric:
            q_nums = extract_numbers(question)
            docs.sort(key=lambda d: len(q_nums & extract_numbers(d.page_content)), reverse=True)

        return docs
