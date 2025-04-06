import json
from pathlib import Path
from langchain_core.documents import Document

def load_structured_json(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    all_chunks = []
    for page_data in data:
        page_number = page_data.get("page")
        items = page_data.get("items", [])
        current_title = None
        buffer = []

        for item in items:
            if item.get("type") == "heading":
                # Flush previous chunk
                if buffer and current_title:
                    all_chunks.append(Document(
                        page_content="\n".join(buffer),
                        metadata={
                            "title": current_title,
                            "page": page_number
                        }
                    ))
                    buffer = []

                current_title = item.get("value", "Untitled")

            elif item.get("type") == "text":
                buffer.append(item.get("value", ""))

        # Flush final buffer for page
        if buffer and current_title:
            all_chunks.append(Document(
                page_content="\n".join(buffer),
                metadata={
                    "title": current_title,
                    "page": page_number
                }
            ))

    return all_chunks
