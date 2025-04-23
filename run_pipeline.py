import json
from pathlib import Path
import os
from tools.data_tools import create_db
from tools.table_tools import extract_table_summary
from tools.qa_tools import compute_qa_answer

try:
    from langsmith import traceable
except ImportError:
    def traceable(func): return func

@traceable
def run_pipeline(source_path: str):
    correct, total, failed, skipped = 0, 0, 0, 0
    with open(source_path, "r") as f:
        data = json.load(f)
    for idx, sample in enumerate(data):
        if "qa" not in sample or "program" not in sample["qa"]:
            print(f"⏭️ Skipping sample {idx} — missing 'qa' or 'qa.program'")
            skipped += 1
            continue

        total += 1
        print(f"\n🔎 Evaluating sample {idx+1}: {sample['qa']['question']}")

        result_2 = extract_table_summary.invoke({"sample": sample})
        result_3 = compute_qa_answer.invoke({"sample": sample})
        predicted = result_3.get("predicted_answer")
        expected = sample["qa"]["answer"]

        if predicted == expected:
            correct += 1
            print("✅ Answer correct")
        else:
            failed += 1
            print(f"❌ Mismatch: predicted={predicted} | expected={expected}")

        create_db.invoke({"input_data": {**result_3, "table_summary": result_2.get("summary", [])}})

    print("\n📊 Final Evaluation Summary")
    print(f"✅ Correct: {correct}")
    print(f"❌ Incorrect: {failed}")
    print(f"⏭️ Skipped: {skipped}")
    print(f"📦 Total Evaluated: {total}")
    print(f"📈 Accuracy: {round((correct / total) * 100, 2) if total else 0}%")

if __name__ == "__main__":
    run_pipeline("train_turn_small.json")

