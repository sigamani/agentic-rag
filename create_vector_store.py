from constants import PDF_FILE, TEXT_FILE, CHROMA_DB_DIR
from embedder import embed_documents
from chunkers import get_chunker
import os
from unstructured.partition.pdf import partition_pdf

def extract_clean_text_from_pdf(input_pdf_path: str, output_txt_path: str):
    # Partition PDF into elements (headings, paragraphs, etc.)
    elements = partition_pdf(filename=input_pdf_path, strategy="hi_res")
    # Join all text content
    text_blocks = [el.text.strip() for el in elements if el.text]
    full_text = "\n\n".join(text_blocks)

    # Write cleaned text to .txt file
    os.makedirs(os.path.dirname(output_txt_path), exist_ok=True)
    with open(output_txt_path, "w", encoding="utf-8") as f:
        f.write(full_text)

    print(f"✅ Extracted clean text to {output_txt_path} with {len(text_blocks)} blocks.")


def chunk_txt_to_docs(txt_path: str, strategy: str = "semantic"):
    if not os.path.exists(txt_path):
        raise FileNotFoundError(f"Text file not found: {txt_path}")

    with open(txt_path, "r", encoding="utf-8") as f:
        raw_text = f.read()

    chunker = get_chunker(strategy)
    return chunker.create_documents(raw_text)


def vector_store_exists(path=CHROMA_DB_DIR) -> bool:
    return os.path.exists(path) and os.path.isdir(path)


def create_vector_store(pdf_path=PDF_FILE, txt_path=TEXT_FILE, strategy="agentic", overwrite=False):
    if not overwrite and vector_store_exists():
        print("[yellow]⚠️ Vector store already exists. Skipping parsing/chunking/embedding.[/yellow]")
        from langchain_chroma import Chroma
        from langchain_ollama import OllamaEmbeddings
        from constants import COLLECTION_NAME, EMBED_MODEL
        return [], Chroma(persist_directory=CHROMA_DB_DIR, collection_name=COLLECTION_NAME, embedding_function=OllamaEmbeddings(model=EMBED_MODEL))

    parse_pdf_to_txt = extract_clean_text_from_pdf(pdf_path, txt_path)
    docs = chunk_txt_to_docs(txt_path, strategy=strategy)
    vectordb = embed_documents(docs, overwrite=True)
    return docs, vectordb

if __name__ == "__main__":
    create_vector_store()
