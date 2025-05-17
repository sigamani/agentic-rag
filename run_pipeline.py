from langchain.tools import tool
from pathlib import Path
import json

try:
    from langsmith import traceable
except ImportError:
    def traceable(func): return func

class DatasetLoader:
    def __init__(self, path: str):
        self.path = path

    def load_jsonl(self):
        with open(self.path, 'r') as f:
            return [json.loads(line) for line in f if line.strip()]

@traceable
@tool
def load_dataset(input_path: str) -> dict:
    """Load a JSONL file and return the first 3 examples for inspection."""
    loader = DatasetLoader(input_path)
    data = loader.load_jsonl()
    return {"data": data[:3], "count": len(data)}

@traceable
@tool
def parse_table_entry(entry: dict) -> dict:
    """Mock parse a table entry to structured JSON with fields and yearly values."""
    parsed_table = {
        "fields": ["revenue", "net_income"],
        "values": [
            {"year": 2021, "revenue": 1_200_000, "net_income": 250_000},
            {"year": 2022, "revenue": 1_450_000, "net_income": 310_000}
        ]
    }
    return {"parsed_table": parsed_table, "id": entry.get("id", "example_1")}

@traceable
@tool
def inject_chain_of_thought(parsed: dict) -> dict:
    """Inject reasoning and a DSL program for a parsed table entry."""
    return {
        "id": parsed.get("id"),
        "reasoning": "Subtract last year net income from current, divide by last year to get growth %.",
        "program": "subtract(310000, 250000), divide(#0, 250000)"
    }

@traceable
@tool
def curate_reasoning(entry: dict) -> dict:
    """Approve reasoning only if both 'subtract' and 'divide' are found in the DSL program."""
    program = entry.get("program", "")
    if "subtract" in program and "divide" in program:
        return {"approved": True, "entry": entry}
    return {"approved": False, "reason": "Program too shallow"}

@traceable
@tool
def save_curated_output(payload: dict) -> dict:
    """Write approved entries to curated_dataset.jsonl. Skip otherwise."""
    if not payload.get("approved"):
        return {"status": "skipped"}
    output_path = Path("curated_dataset.jsonl")
    with open(output_path, "a") as f:
        json.dump(payload["entry"], f)
        f.write("\n")
    return {"status": "written", "file": str(output_path)}
