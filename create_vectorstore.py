import json
import logging
from pathlib import Path
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_core.documents import Document
from constants import EMBED_MODEL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

jsonl_dir = Path("documents/extract")
vectorstore_dir = Path("vectorstore")
vectorstore_dir.mkdir(parents=True, exist_ok=True)
embedder = OllamaEmbeddings(model=EMBED_MODEL)

def load_chunks(file: Path) -> list[dict]:
    return [json.loads(line) for line in file.open()]

def to_documents(file: Path, chunks: list[dict]) -> list[Document]:
    return [
        Document(
            page_content=chunk.get("text", ""),
            metadata={
                "document_id": Path(chunk.get("metadata", {}).get("document_path", file.name)).stem,
                **{
                    k: chunk.get("metadata", {}).get(k)
                    for k in ("page_number", "element_type", "document_path")
                },
            },
        )
        for chunk in chunks
    ]

def main():
    docs = [
        doc
        for file in jsonl_dir.glob("*.jsonl")
        for doc in to_documents(file, load_chunks(file))
    ]
    logger.info(f"Indexing {len(docs)} documents...")
    Chroma.from_documents(docs, embedder, persist_directory=str(vectorstore_dir))
    logger.info("✅ Vectorstore built and saved.")

if __name__ == "__main__":
    main()
