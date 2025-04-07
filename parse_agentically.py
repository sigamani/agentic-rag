
import fitz
import json
from pathlib import Path
from typing import List
from time import time
from langchain.docstore.document import Document
from utils.agentic_chunker import split_with_llm
from datetime import datetime

SOURCE_PATH = "data/whirlpool.pdf"
OUTPUT_PATH = "data/agentic_chunks.json"

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def extract_sections_from_pdf(pdf_path: str) -> List[Document]:
    doc = fitz.open(pdf_path)
    all_chunks = []
    for i, page in enumerate(doc):
        log(f"Processing page {i+1}/{len(doc)}...")
        text = page.get_text()
        paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 20]
        for para in paragraphs:
            enriched_chunks = split_with_llm(para, page=i+1, title=f"Page {i+1}")
            for enriched in enriched_chunks:
                all_chunks.append(Document(
                    page_content=enriched["text"],
                    metadata=enriched["metadata"]
                ))
        log(f"Page {i+1} complete. Total chunks so far: {len(all_chunks)}")
    return all_chunks

def save_chunks_as_json(docs: List[Document], output_path: str):
    payload = []
    for doc in docs:
        payload.append({
            "text": doc.page_content,
            "metadata": doc.metadata
        })
    with open(output_path, "w") as f:
        json.dump(payload, f, indent=2)
    log(f"Saved {len(docs)} chunks to: {output_path}")

if __name__ == "__main__":
    start = time()
    log("⏳ Starting agentic chunking of PDF...")
    documents = extract_sections_from_pdf(SOURCE_PATH)
    save_chunks_as_json(documents, OUTPUT_PATH)
    duration = time() - start
    log(f"✅ Done. Total time: {duration:.2f} seconds ({duration/60:.1f} mins)")
