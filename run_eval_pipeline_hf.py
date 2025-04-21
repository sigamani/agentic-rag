
import os
import json
import subprocess
from datasets import load_dataset
from datetime import datetime
from prompts import generate_answer_and_program_prompt

from langchain.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_community.llms import OpenAI  # replace with your preferred LLM

# Prompt + output parser
parser = JsonOutputParser()
prompt = PromptTemplate.from_template(generate_answer_and_program_prompt)
llm = OpenAI(model="gpt-4", temperature=0)  # can switch to any compatible LangChain LLM

def format_table_as_text(table_rows):
    if not table_rows:
        return "No table provided."
    header = table_rows[0]
    body = table_rows[1:]
    output = ["| " + " | ".join(header) + " |", "| " + " | ".join(["---"] * len(header)) + " |"]
    for row in body:
        output.append("| " + " | ".join(str(x) for x in row) + " |")
    return "\n".join(output)

def generate_answer_and_program(example):
    question = example.get("qa", {}).get("question") or example.get("question") or "What is the answer?"
    table = format_table_as_text(example.get("table", []))

    formatted_prompt = prompt.format_prompt(question=question, table=table)
    try:
        response = llm.invoke(formatted_prompt.to_string())
        return parser.parse(response)
    except Exception:
        return {"answer": "ERROR", "program": ""}

def main():
    from datasets import load_dataset
    dataset = load_dataset("TheFinAI/CONVFINQA_test_test", split="train")
    total = len(dataset)

    test_size = min(1500, total)
    split_index = total - test_size
    test_dataset = dataset.select(range(split_index, total))

    predictions = []
    for row in test_dataset:
        generated = generate_answer_and_program(row)
        predictions.append({
            "id": row["id"],
            "answer": generated["answer"],
            "program": generated.get("program", "")
        })

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
