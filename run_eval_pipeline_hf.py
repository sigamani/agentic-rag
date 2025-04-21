import os
import json
import subprocess
from datasets import load_dataset
from datetime import datetime
from graph import graph

# Initialize LLM once
from langchain_together import ChatTogether
from langsmith import traceable

LLM_API_KEY = "f2ca76b85d77e125667559d3bbb282901dbb80d89af2f9831e6de303a532a2f0"
LLM_API_BASE = "https://api.together.xyz/v1"
MODEL_NAME = "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"

llm_model = ChatTogether(
    model=MODEL_NAME,
    together_api_key=LLM_API_KEY,
    base_url=LLM_API_BASE,
    temperature=0
)


def generate_answer_and_program(example):
    question = example['question']
    table = example['table']
    history = example.get('history', [])

    # Generate program using model
    program = llm_model.generate_program(question, table, history)

    # Execute program to get final answer
    graph = Graph(table)
    answer = graph.execute(program)

    return {
        "answer": answer,
        "program": program
    }

def main():
    dataset = load_dataset("TheFinAI/CONVFINQA_test_test", split="val")
    total = len(dataset)

    test_size = min(1500, total)
    split_index = total - test_size
    test_dataset = dataset.select(range(split_index, total))

    # Generate predictions from model
    predictions = []
    for row in test_dataset:
        generated = generate_answer_and_program(row)
        predictions.append({
            "id": row["id"],
            "answer": generated["answer"],
            "program": generated.get("program", "")
        })

    # Use same data as reference set for now (can be improved)
    references = [
        {"id": row["id"], "answer": row["answer"], "program": row.get("program", "")}
        for row in test_dataset
    ]

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
