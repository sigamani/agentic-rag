# pip install "trl==0.4.7" "transformers==4.36.2"
import torch
from unsloth import FastLanguageModel
from datasets import load_dataset
from transformers import TrainingArguments
from trl import SFTTrainer

# Load the model and tokenizer
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="./merged_tat_llm_fp16",
    max_seq_length=4096,
    dtype=torch.bfloat16,  # Use bfloat16 as recommended by Unsloth
    load_in_4bit=True,
)

# Prepare the dataset
dataset = load_dataset("json", data_files="/workspace/fine-tuning/convfinqa_sft_axolotl.jsonl", split="train")

# Define a prompt template
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

# Apply LoRA configuration directly via get_peft_model
model = FastLanguageModel.get_peft_model(
    model,
    r=16,
    lora_alpha=32,
    lora_dropout=0.0,  # Set to 0 for optimized patching
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    bias="none",
    use_gradient_checkpointing="unsloth",  # Enable Unsloth's gradient checkpointing
    random_state=42,
)

# Define training arguments
training_args = TrainingArguments(
    output_dir="tat_llm_convfinqa",
    per_device_train_batch_size=4,
    gradient_accumulation_steps=8,
    num_train_epochs=3,
    learning_rate=2e-5,
    bf16=True,  # Use bfloat16 for training
    logging_steps=10,
    save_steps=100,
    save_total_limit=2,
    evaluation_strategy="no",
)

# Initialize the trainer
trainer = SFTTrainer(
    model=model,
    train_dataset=dataset,
    dataset_text_field="text",
    tokenizer=tokenizer,
    args=training_args,
)

# Start training
trainer.train()

# Save the fine-tuned model
model.save_pretrained("tat_llm_convfinqa")
tokenizer.save_pretrained("tat_llm_convfinqa") 
