import torch
from unsloth import FastLanguageModel, PatchTrainer
from datasets import load_dataset
from transformers import TrainingArguments

# === Load Base Model ===
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="./merged_tat_llm_fp16",
    max_seq_length=4096,
    dtype=torch.bfloat16,
    load_in_4bit=True,
)

# === Load Dataset ===
dataset = load_dataset("TheFinAI/CONVFINQA_train", split="train")

# === Filter only valid samples ===
dataset = dataset.filter(lambda ex: "qa" in ex and "exe_ans" in ex["qa"])

# === Format with CoT ===
def format_with_cot(example):
    history = " ".join(example.get("cur_dial", []))
    question = example["qa"].get("question", "")
    answer = example["qa"].get("exe_ans", "")
    gold_program = example["qa"].get("gold_program", [])

    return {
        "instruction": "Answer the financial question using step-by-step reasoning.",
        "input": f"{history}\n\nQuestion: {question}".strip(),
        "output": f"Let's think step by step.\nProgram: {gold_program}\nAnswer: {answer}"
    }

dataset = dataset.map(format_with_cot)

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

# === Training Args ===
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
    evaluation_strategy="no",
)

# === Trainer ===
trainer = PatchTrainer(
    model=model,
    train_dataset=dataset,
    tokenizer=tokenizer,
    dataset_text_field="text",
    args=training_args,
)

trainer.train()

# === Save Final Model ===
model.save_pretrained("tat_llm_convfinqa_cot")
tokenizer.save_pretrained("tat_llm_convfinqa_cot")
