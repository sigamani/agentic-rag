import json
from pathlib import Path
import os
from data_tools import create_db
from table_tools import extract_table_summary
from qa_tools import compute_qa_answer

try:
    from langsmith import traceable
except ImportError:
    def traceable(func): return func

@traceable
def run_pipeline(source_path: str):
    correct, total, failed = 0, 0, 0
    with open(source_path, "r") as f:
        data = json.load(f)
    for idx, sample in enumerate(data):
        total += 1
        result_2 = extract_table_summary.run(sample=sample)
        result_3 = compute_qa_answer.run(sample=sample)
        predicted = result_3.get("predicted_answer")
        expected = sample["qa"]["answer"]
        if predicted == expected: correct += 1
        else: failed += 1
        create_db.run(input_data={**result_3, "table_summary": result_2.get("summary", [])})
    print(f"\nAccuracy: {round((correct / total) * 100, 2)}%")

if __name__ == "__main__":
    run_pipeline("train_turn_small.json")
