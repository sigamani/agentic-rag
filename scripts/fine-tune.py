import json
import torch
from transformers import TrainingArguments
from trl import SFTTrainer
from unsloth import FastLanguageModel
from datasets import Dataset

# === Load and Filter ===
with open("data/train_curated.jsonl", "r") as f:
    raw_data = [json.loads(line) for line in f if line.strip()]

# === Curriculum partition by program length ===
def categorize(example):
    program = example.get("Program", "")
    length = len(program.split())
    if length < 5:
        return "easy"
    elif length < 15:
        return "medium"
    return "hard"

categorized = {"easy": [], "medium": [], "hard": []}
for ex in raw_data:
    category = categorize(ex)
    categorized[category].append(ex)

# === Format and convert to dataset ===
def format_with_cot(example):
    reasoning_template = f"""
You are a financial reasoning assistant.

Given a question based on a financial report (with pre-text, post-text, and table snippets), think step-by-step to identify the right values and apply the correct calculation.

Always follow this format:

Step 1: Rephrase the question for clarity.  
Step 2: Identify key values from the table or context.  
Step 3: Apply the correct operation (e.g., subtraction, percentage change).  
Step 4: Compute the result.  
Final Answer: <answer as a single number in float format>

Question: {example['input']}

Step 1: Let's rephrase the question.  
Step 2: We need to find relevant values.  
Step 3: We apply: {example.get("Program", "")}  
Step 4: Result of calculation.  
Final Answer: {example.get("Final Answer", "")}
"""
    return {
        "instruction": example["instruction"],
        "input": example["input"],
        "output": reasoning_template,
    }

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

# Apply formatting + merging
datasets = {}
for k in categorized:
    formatted = list(map(format_with_cot, categorized[k]))
    ds = Dataset.from_list(formatted).map(merge_fields)
    datasets[k] = ds

print(f"[✅ DEBUG] Easy: {len(datasets['easy'])} | Medium: {len(datasets['medium'])} | Hard: {len(datasets['hard'])}")

# === Load Base Model ===
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="./merged_tat_llm_fp16",
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

# 🔧 Enable logits for training
import os
os.environ['UNSLOTH_RETURN_LOGITS'] = '1'

# === Curriculum loop over epochs ===
curriculum = [("easy", 1), ("medium", 1), ("hard", 1)]

for phase, epochs in curriculum:
    print(f"\n📚 Training on {phase} set for {epochs} epoch(s)...")
    training_args = TrainingArguments(
        output_dir=f"tat_llm_{phase}",
        per_device_train_batch_size=4,
        gradient_accumulation_steps=8,
        num_train_epochs=epochs,
        learning_rate=2e-5,
        bf16=True,
        logging_steps=1,
        save_steps=25,
        save_total_limit=2,
    )
    trainer = SFTTrainer(
        model=model,
        train_dataset=datasets[phase],
        tokenizer=tokenizer,
        args=training_args,
    )
    trainer.train()

# === Save Final Model ===
model.save_pretrained("tat_llm_convfinqa_curriculum")
tokenizer.save_pretrained("tat_llm_convfinqa_curriculum")
