
import os
import json
import subprocess
from datasets import load_dataset
from datetime import datetime

def main():
    # Load full val set from HF
    dataset = load_dataset("TheFinAI/CONVFINQA_test_test", split="val")
    total = len(dataset)

    # Use last 1500 as test
    test_size = 1500
    train_dataset = dataset.select(range(0, total - test_size))
    test_dataset = dataset.select(range(total - test_size, total))

    # Construct references from test set
    references = [
        {"id": row["id"], "answer": row["answer"], "program": row.get("program", "")}
        for row in test_dataset
    ]

    # TODO: Replace with actual model predictions
    predictions = [
        {"id": row["id"], "answer": row["answer"], "program": row.get("program", "")}
        for row in test_dataset
    ]

    # Save to disk
    output_dir = "eval_outputs"
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pred_file = os.path.join(output_dir, f"preds_{timestamp}.jsonl")
    ref_file = os.path.join(output_dir, f"refs_{timestamp}.jsonl")

    with open(pred_file, "w") as f:
        for item in predictions:
            f.write(json.dumps(item) + "\n")

    with open(ref_file, "w") as f:
        for item in references:
            f.write(json.dumps(item) + "\n")

    # Evaluate
    cmd = [
        "python3",
        "evaluator_full.py",
        "--pred_file", pred_file,
        "--ref_file", ref_file,
        "--use_langsmith",
        "--project", "convfinqa-eval"
    ]
    print("Running:", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True)
    print("--- STDOUT ---")
    print(result.stdout)
    if result.stderr:
        print("--- STDERR ---")
        print(result.stderr)


if __name__ == "__main__":
    main()
