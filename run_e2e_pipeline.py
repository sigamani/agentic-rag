import json
from datasets import load_dataset
from datetime import datetime
import os
import subprocess

def generate_dummy_predictions(refs):
    # Simulate model output by copying gold answers (perfect predictions)
    return [
        {"id": r["id"], "answer": r["answer"], "program": r["program"]}
        for r in refs
    ]

def load_test_data():
    dataset = load_dataset("TheFinAI/CONVFINQA_test_test", split="test")
    references = [
        {"id": row["id"], "answer": row["answer"], "program": row["program"]}
        for row in dataset
    ]
    return references

def run_evaluation(predictions, references, output_dir="eval_outputs", project_name="convfinqa-eval"):
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pred_file = os.path.join(output_dir, f"preds_{timestamp}.jsonl")
    ref_file = os.path.join(output_dir, f"refs_{timestamp}.jsonl")

    with open(pred_file, "w") as f:
        for p in predictions:
            f.write(json.dumps(p) + "\n")

    with open(ref_file, "w") as f:
        for r in references:
            f.write(json.dumps(r) + "\n")

    cmd = [
        "python3",
        "evaluator_full.py",
        "--pred_file", pred_file,
        "--ref_file", ref_file,
        "--use_langsmith",
        "--project", project_name
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    print("---- Evaluation Output ----")
    print(result.stdout)
    if result.stderr:
        print("---- STDERR ----")
        print(result.stderr)


if __name__ == "__main__":
    print("Loading test data...")
    refs = load_test_data()

    print("Generating dummy predictions...")
    preds = generate_dummy_predictions(refs)

    print("Running evaluator_full.py with LangSmith logging...")
    run_evaluation(preds, refs)
