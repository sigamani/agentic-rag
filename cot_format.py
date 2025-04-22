from datasets import load_dataset

# Load small slice for testing
dataset = load_dataset("TheFinAI/CONVFINQA_train", split="train[:5]")

def format_with_cot(example):
    if "qa" not in example:
        return {
            "instruction": "N/A",
            "input": "",
            "output": "N/A"
        }

    history = " ".join(example.get("cur_dial", []))
    question = example["qa"].get("question", "")
    answer = example["qa"].get("exe_ans", "")
    gold_program = example["qa"].get("gold_program", [])

    return {
        "instruction": "Answer the financial question using step-by-step reasoning.",
        "input": f"{history}\n\nQuestion: {question}".strip(),
        "output": f"Let's think step by step.\nProgram: {gold_program}\nAnswer: {answer}"
    }
formatted = dataset.map(format_with_cot)
dataset = dataset.filter(lambda ex: "qa" in ex and "exe_ans" in ex["qa"])
print(formatted[0])
