import fitz  # PyMuPDF
import json
from pathlib import Path
from utils.structure_aware_chunker import StructureAwareChunker
from langchain.docstore.document import Document
from time import time
from datetime import datetime

PDF_PATH = "data/whirlpool.pdf"
OUTPUT_PATH = "data/structure_chunks.jsonl"

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def parse_pdf_to_jsonl(pdf_path: str, output_path: str):
    chunker = StructureAwareChunker()
    doc = fitz.open(pdf_path)
    total_chunks = 0

    with open(output_path, "w") as out:
        for i, page in enumerate(doc):
            log(f"🔍 Page {i+1}/{len(doc)}")
            text = page.get_text()
            if not text.strip():
                continue
            try:
                docs = chunker.chunk(text, page=i+1, title=f"Page {i+1}")
                for d in docs:
                    json.dump({
                        "text": d.page_content,
                        "metadata": d.metadata
                    }, out)
                    out.write("\n")
                total_chunks += len(docs)
            except Exception as e:
                log(f"[Error] Failed on page {i+1}: {e}")

    log(f"✅ Done. Total chunks: {total_chunks}")
    log(f"Output written to {output_path}")

if __name__ == "__main__":
    start = time()
    parse_pdf_to_jsonl(PDF_PATH, OUTPUT_PATH)
    duration = time() - start
    log(f"⏱ Total time: {duration:.1f}s ({duration/60:.2f} mins)")
