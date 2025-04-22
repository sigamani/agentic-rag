# pip install "trl==0.4.7" "transformers==4.36.2"
import torch
from unsloth import FastLanguageModel, PatchTrainer
from datasets import load_dataset
from transformers import TrainingArguments

# === Load Model ===
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="./merged_tat_llm_fp16",
    max_seq_length=4096,
    dtype=torch.bfloat16,
    load_in_4bit=True,
)

# === Load and Format Dataset ===
dataset = load_dataset("json", data_files="convfinqa_sft_axolotl.jsonl", split="train")

def format_example(example):
    prompt = f"""### Instruction:
{example['instruction']}

### Input:
{example['input']}

### Response:
{example['output']}"""
    example["text"] = prompt
    return example

dataset = dataset.map(format_example)

# === Apply LoRA ===
model = FastLanguageModel.get_peft_model(
    model,
    r=16,
    lora_alpha=32,
    lora_dropout=0.0,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    bias="none",
    task_type="CAUSAL_LM",
    use_gradient_checkpointing="unsloth",
    random_state=42,
)

# === Training Configuration ===
training_args = TrainingArguments(
    output_dir="tat_llm_convfinqa",
    per_device_train_batch_size=4,
    gradient_accumulation_steps=8,
    num_train_epochs=3,
    learning_rate=2e-5,
    bf16=True,
    logging_steps=1,
    save_steps=25,
    save_total_limit=2,
    evaluation_strategy="no",
)

# === Use PatchTrainer (instead of SFTTrainer) ===
trainer = PatchTrainer(
    model=model,
    train_dataset=dataset,
    tokenizer=tokenizer,
    dataset_text_field="text",
    args=training_args,
)

trainer.train()

# === Save the Model ===
model.save_pretrained("tat_llm_convfinqa")
tokenizer.save_pretrained("tat_llm_convfinqa")
