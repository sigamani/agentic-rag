from langchain.tools import tool
import json
from pathlib import Path

@tool
def create_dataset(source_path: str) -> dict:
    """Loads and returns the first QA example from a ConvFinQA-style dataset."""
    with open(source_path, "r") as f:
        lines = [json.loads(line) for line in f if line.strip()]
    return {"sample": lines[0], "total": len(lines)}

@tool
def create_db(input_data: dict) -> dict:
    """Appends the given input dictionary to qa_results.jsonl."""
    path = Path("qa_results.jsonl")
    with open(path, "a") as f:
        json.dump(input_data, f)
        f.write("\n")
    return {"status": "written", "path": str(path)}
