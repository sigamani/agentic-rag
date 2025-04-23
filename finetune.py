import os
import torch
from datasets import load_dataset, concatenate_datasets
from transformers import TrainingArguments
from trl import SFTTrainer
from unsloth import FastLanguageModel


# === Load Easy + Hard Sets ===
easy = load_dataset("michael-sigamani/Oscar-ConvFinQA", data_files="train_curated.jsonl", split="train")
hard = load_dataset("michael-sigamani/Oscar-ConvFinQA", data_files="rejected_examples.jsonl", split="train")

easy = easy.map(lambda x: {"difficulty": "easy"})
hard = hard.map(lambda x: {"difficulty": "hard"})

# === Format with CoT ===
def format_with_cot(example):
    instruction = "Answer the financial question using step-by-step reasoning."
    question = example.get("input") or example.get("question", "")
    answer = example.get("Final Answer") or example.get("answer", "")
    gold_program = example.get("Program") or example.get("program", "")

    steps = f"""
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
""".strip()

    return {
        "difficulty": example["difficulty"],
        "instruction": instruction,
        "input": question,
        "output": steps,
    }

def format_hard_with_prompt(example):
    base = format_with_cot(example)
    base["instruction"] += "\n\n⚠️ If any key numbers are missing, ask the user for clarification instead of hallucinating values."
    return base

easy = easy.map(format_with_cot)
hard = hard.map(format_hard_with_prompt)

# === Merge + Tokenization ===
dataset = concatenate_datasets([easy, hard])
dataset = dataset.map(lambda x: {
    "text": f"""### Instruction:
{x['instruction']}

### Input:
{x['input']}

### Response:
{x['output']}"""
})

# === Load Base Model ===
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="./merged_tat_llm_fp16",
    max_seq_length=4096,
    dtype=torch.bfloat16,
    load_in_4bit=True,
)

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

training_args = TrainingArguments(
    output_dir="tat_llm_curriculum_cot",
    per_device_train_batch_size=4,
    gradient_accumulation_steps=8,
    num_train_epochs=2,
    learning_rate=2e-5,
    bf16=True,
    logging_steps=1,
    save_steps=25,
    save_total_limit=2,
)

os.environ['UNSLOTH_RETURN_LOGITS'] = '1'

trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    args=training_args,
    dataset_text_field="text",
)

trainer.train()
model.save_pretrained("tat_llm_curriculum_cot_final")
tokenizer.save_pretrained("tat_llm_curriculum_cot_final")
