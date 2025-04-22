import json
import torch
from transformers import TrainingArguments
from trl import SFTTrainer
from unsloth import FastLanguageModel
from datasets import Dataset


# === Load and Filter ===
with open("data/train_turn.json", "r") as f:
    try:
        raw_data = json.load(f)  # For full JSON object or list
    except json.JSONDecodeError:
        f.seek(0)
        raw_data = [json.loads(line) for line in f if line.strip()]  # For JSONL fallback

def is_valid(example):
    return (
        "qa" in example and
        "exe_ans" in example["qa"] and
        isinstance(example["qa"]["exe_ans"], str) and
        example["qa"]["exe_ans"].strip() != ""
    )

def format_with_cot(example):
    history = " ".join(example.get("cur_dial", []))
    question = example["qa"].get("question", "")
    answer = example["qa"].get("exe_ans", "")
    gold_program = example["qa"].get("program_re", example["qa"].get("program", ""))

    reasoning_template = f"""
	You are a financial reasoning assistant.

	Given a question based on a financial report (with pre-text, post-text, and table snippets), think step-by-step to identify the right values and apply the correct calculation.

	Always follow this format:

	Step 1: Rephrase the question for clarity.  
	Step 2: Identify key values from the table or context.  
	Step 3: Apply the correct operation (e.g., subtraction, percentage change).  
	Step 4: Compute the result.  
	Final Answer: <answer as a single number in float format>

	Question: {question}

	Step 1: Let's rephrase the question.  
	Step 2: We need to find relevant values.  
	Step 3: We apply: {gold_program}  
	Step 4: Result of calculation.  
	Final Answer: {answer}
    """
    return {
        "instruction": "Answer the financial question using step-by-step reasoning.",
        "input": f"{history}\n\nQuestion: {question}".strip(),
        "output": reasoning_template
    }


filtered = list(filter(is_valid, raw_data))
formatted = list(map(format_with_cot, filtered))
dataset = Dataset.from_list(formatted)

# Add a combined 'text' field that SFTTrainer expects
def merge_fields(example):
    example["text"] = f"""
    ### Instruction:
    {example['instruction']}

    ### Input:
    {example['input']}

    ### Response:
    {example['output']}
    """
    return example

dataset = dataset.map(merge_fields)

print(f"[✅ DEBUG] Loaded {len(dataset)} formatted examples")

# === Load Base Model ===
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="../ConvFinQA2/merged_tat_llm_fp16",
    max_seq_length=4096,
    dtype=torch.bfloat16,
    load_in_4bit=True,
)

# === Apply LoRA ===
model = FastLanguageModel.get_peft_model(
    model,
    r=16,
    lora_alpha=32,
    lora_dropout=0.0,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    bias="none",
    use_gradient_checkpointing="unsloth",
    random_state=42,
)

# === Training Arguments ===
training_args = TrainingArguments(
    output_dir="tat_llm_convfinqa_cot",
    per_device_train_batch_size=4,
    gradient_accumulation_steps=8,
    num_train_epochs=3,
    learning_rate=2e-5,
    bf16=True,
    logging_steps=1,
    save_steps=25,
    save_total_limit=2,
)

# === Trainer ===
trainer = SFTTrainer(
    model=model,
    train_dataset=dataset,
    tokenizer=tokenizer,
    args=training_args,
)

# 🔧 Enable logits for training
import os
os.environ['UNSLOTH_RETURN_LOGITS'] = '1'

trainer.train()

# === Save Final Model ===
model.save_pretrained("tat_llm_convfinqa_cot")
tokenizer.save_pretrained("tat_llm_convfinqa_cot")
