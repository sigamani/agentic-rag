import json
import os
import torch
from transformers import TrainingArguments
from trl import SFTTrainer
from unsloth import FastLanguageModel
from datasets import Dataset

# === Load Curriculum Data ===
with open("data/curriculum_generated.jsonl", "r") as f:
    raw_data = [json.loads(line) for line in f if line.strip()]

def classify_difficulty(example):
    program = example.get("Program", "")
    length = len(program.split())
    if length <= 5:
        return "easy"
    elif length <= 12:
        return "medium"
    else:
        return "hard"

def format_example(example):
    program = example.get("Program", "")
    answer = example.get("Final Answer", "")
    question = example.get("input", "")
    instruction = example.get("instruction", "")

    reasoning = f"""
You are a financial reasoning assistant.

Given a question based on a financial report, think step-by-step to identify the right values and apply the correct calculation.

Always follow this format:
Step 1: Rephrase the question for clarity.  
Step 2: Identify key values from the table or context.  
Step 3: Apply the correct operation (e.g., subtraction, percentage change).  
Step 4: Compute the result.  
Final Answer: <answer as a single number in float format>

Question: {question}

Step 1: Let's rephrase the question.  
Step 2: We need to find relevant values.  
Step 3: We apply: {program}  
Step 4: Result of calculation.  
Final Answer: {answer}
"""
    return {
        "instruction": instruction,
        "input": question,
        "output": reasoning,
        "difficulty": classify_difficulty(example)
    }

formatted = list(map(format_example, raw_data))

# === Split by Difficulty ===
easy = Dataset.from_list([ex for ex in formatted if ex["difficulty"] == "easy"])
medium = Dataset.from_list([ex for ex in formatted if ex["difficulty"] == "medium"])
hard = Dataset.from_list([ex for ex in formatted if ex["difficulty"] == "hard"])

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

easy = easy.map(merge_fields)
medium = medium.map(merge_fields)
hard = hard.map(merge_fields)

print(f"[✅ Loaded] {len(easy)} easy, {len(medium)} medium, {len(hard)} hard examples")

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

# === Training Arguments ===
training_args = TrainingArguments(
    output_dir="tat_llm_curriculum",
    per_device_train_batch_size=4,
    gradient_accumulation_steps=8,
    learning_rate=2e-5,
    bf16=True,
    logging_steps=1,
    save_steps=25,
    save_total_limit=2,
)

os.environ["UNSLOTH_RETURN_LOGITS"] = "1"

# === Training Loop with Curriculum ===
def run_stage(name, dataset, epochs):
    print(f"[🎯 Training {name.upper()} set for {epochs} epoch(s)]")
    trainer = SFTTrainer(
        model=model,
        train_dataset=dataset,
        tokenizer=tokenizer,
        args=training_args,
    )
    trainer.args.num_train_epochs = epochs
    trainer.train()

run_stage("easy", easy, 1)
run_stage("medium", medium, 1)
run_stage("hard", hard, 1)

# === Save Final Model ===
model.save_pretrained("tat_llm_curriculum")
tokenizer.save_pretrained("tat_llm_curriculum")
