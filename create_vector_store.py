from constants import PDF_FILE, TEXT_FILE, CHROMA_DB_DIR
from parser import parse_pdf_to_txt, chunk_txt_to_docs
from embedder import embed_documents
import os

def vector_store_exists(path=CHROMA_DB_DIR) -> bool:
    return os.path.exists(path) and os.path.isdir(path)

def create_vector_store(pdf_path=PDF_FILE, txt_path=TEXT_FILE, strategy="semantic", overwrite=False):
    if not overwrite and vector_store_exists():
        print("[yellow]⚠️ Vector store already exists. Skipping parsing/chunking/embedding.[/yellow]")
        from langchain_community.vectorstores import Chroma
        from langchain_ollama import OllamaEmbeddings
        from constants import COLLECTION_NAME, EMBED_MODEL
        return [], Chroma(persist_directory=CHROMA_DB_DIR, collection_name=COLLECTION_NAME, embedding_function=OllamaEmbeddings(model=EMBED_MODEL))

    parse_pdf_to_txt(pdf_path, txt_path)
    docs = chunk_txt_to_docs(txt_path, strategy=strategy)
    vectordb = embed_documents(docs, overwrite=True)
    return docs, vectordb

if __name__ == "__main__":
    create_vector_store()
