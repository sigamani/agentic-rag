from langchain.tools import tool
from pathlib import Path
import json
from typing import List, Dict
from pydantic import BaseModel, ValidationError

try:
    from langsmith import traceable
except ImportError:
    def traceable(func): return func

# ------------------ Pydantic Schemas ------------------

class ParsedTable(BaseModel):
    """Schema for parsed financial table with numeric fields."""
    fields: List[str]
    values: List[Dict[str, float]]

class ReasoningEntry(BaseModel):
    """Schema for LLM-generated reasoning and program."""
    id: str
    reasoning: str
    program: str

class CuratedPayload(BaseModel):
    """Schema for approved entries being saved to JSONL."""
    approved: bool
    entry: ReasoningEntry

# ------------------ Utility Classes ------------------

class DatasetLoader:
    def __init__(self, path: str):
        self.path = path

    def load_jsonl(self):
        with open(self.path, 'r') as f:
            return [json.loads(line) for line in f if line.strip()]

# ------------------ LangChain Tools ------------------

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
    try:
        ParsedTable(**parsed_table)
    except ValidationError as e:
        return {"error": str(e)}
    return {"parsed_table": parsed_table, "id": entry.get("id", "example_1")}

@traceable
@tool
def inject_chain_of_thought(parsed: dict) -> dict:
    """Inject reasoning and a DSL program for a parsed table entry."""
    entry = {
        "id": parsed.get("id"),
        "reasoning": "Subtract last year net income from current, divide by last year to get growth %.",
        "program": "subtract(310000, 250000), divide(#0, 250000)"
    }
    try:
        ReasoningEntry(**entry)
    except ValidationError as e:
        return {"error": str(e)}
    return entry

@traceable
@tool
def curate_reasoning(entry: dict) -> dict:
    """Approve reasoning only if both 'subtract' and 'divide' are found in the DSL program."""
    try:
        parsed = ReasoningEntry(**entry)
    except ValidationError:
        return {"approved": False, "reason": "Validation failed"}

    program = parsed.program
    if "subtract" in program and "divide" in program:
        return {"approved": True, "entry": parsed.model_dump()}
    return {"approved": False, "reason": "Program too shallow"}

@traceable
@tool
