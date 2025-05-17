# create_db.py

import json
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from pathlib import Path

def parse_llm_extracted_jsonl(filepath, limit=None):
    docs = []
    with open(filepath, 'r') as f:
        for i, line in enumerate(f):
            if limit and i >= limit:
                break
            entry = json.loads(line)
            if "extracted" not in entry:
                continue
            for field in entry["extracted"]:
                try:
                    text = f"{field['name']} of {field['value']} {field['unit']} on {field['date']}. Summary: {field['description']}"
                    doc = Document(
                        page_content=text,
                        metadata={
                            "source_id": field.get("id"),
                            "name": field.get("name"),
                            "value": field.get("value"),
                            "unit": field.get("unit"),
                            "date": field.get("date"),
                            "row": field.get("row"),
                            "doc_id": entry["id"],
                            "description": field.get("description"),
                            "raw_metadata": field.get("metadata")
                        }
                    )
                    docs.append(doc)
                except Exception as e:
                    print(f"Skipping bad field: {e}")
    return docs

if __name__ == "__main__":
    input_file = "extracted.jsonl"
    persist_dir = "chroma_index"
    embedding_model = "nomic-embed-text"

    docs = parse_llm_extracted_jsonl(input_file)

    embeddings = OllamaEmbeddings(model=embedding_model)
    vectordb = Chroma.from_documents(docs, embeddings, persist_directory=persist_dir)
    vectordb.persist()

    print(f"✅ Vector index created with {len(docs)} documents at {persist_dir}")

