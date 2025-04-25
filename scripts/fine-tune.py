import os
import torch
import json
import argparse
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
from transformers import TrainingArguments
from trl import SFTTrainer
from unsloth import FastLanguageModel
from datasets import Dataset

from utils.logging import setup_wandb
from utils.metrics import MetricStabiliser, log_metrics_to_langsmith
from llm_eval_judge import evaluate_final_answer_accuracy_claude as evaluate_final_answer_accuracy

# --- Merge LoRA if Needed ---
def merge_lora_if_needed(base_model_name, lora_adapter_path, merged_save_path):
    if os.path.exists(merged_save_path):
        print(f"[🧹] Merged model already exists at {merged_save_path}, skipping merge.")
        return merged_save_path

    os.makedirs(merged_save_path, exist_ok=True)
    print(f"[🔄] Merging LoRA adapter into base model...")

    base_model = AutoModelForCausalLM.from_pretrained(
        base_model_name,
        torch_dtype=torch.float16,
        device_map="auto",
    )

    merged_model = PeftModel.from_pretrained(base_model, lora_adapter_path)
    merged_model = merged_model.merge_and_unload()

    merged_model.save_pretrained(merged_save_path)
    tokenizer = AutoTokenizer.from_pretrained(base_model_name)
    tokenizer.save_pretrained(merged_save_path)

    print(f"[✅] Merge complete. Saved to {merged_save_path}")
    return merged_save_path

# --- Load Dataset ---
def load_and_format_dataset(filepath):
    with open(filepath, "r") as f:
        raw_data = [json.loads(line) for line in f if line.strip()]

    def format_with_cot(example):
        reasoning_template = f"""
        You are a financial reasoning assistant.
        Given a question based on a financial report, think step-by-step to find the right values and apply calculations.
        Always follow:
        - Step 1: Rephrase the question.
        - Step 2: Identify values.
        - Step 3: Apply {example.get('Program', '')}
        - Step 4: Compute.
        Final Answer: {example.get('Final Answer', '')}
        Question: {example['input']}
        """
        return {
            "instruction": example["instruction"],
            "input": example["input"],
            "output": reasoning_template,
            "Final Answer": example.get("Final Answer", ""),
        }

    formatted = list(map(format_with_cot, raw_data))
    return Dataset.from_list(formatted)

# --- Train Segment ---
def train_segment(trainer, segment, label, max_epochs=5):
    print(f"\n==((====))== Training on {label.upper()} segment...")
    stabiliser = MetricStabiliser(window=3, threshold=0.002)

    for epoch in range(max_epochs):
        trainer.train()
        metrics = trainer.state.log_history[-1]
        loss = metrics.get("loss", 0.0)
        acc = metrics.get("mean_token_accuracy", 0.0)
        claude_score = evaluate_final_answer_accuracy(segment, sample_size=100)

        stabiliser.update(loss, acc, claude_score)

        print(f"[{label.upper()}] Epoch {epoch}: Loss={loss:.4f}, Acc={acc:.4f}, Claude={claude_score:.4f}")
        log_metrics_to_langsmith(segment, trainer.model, label, epoch)

        if stabiliser.should_stop():
            print(f"[⏹ Early Stopping] on {label.upper()} at epoch {epoch}")
            break

# --- Main ---
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base_model", type=str, required=True)
    parser.add_argument("--lora_adapter", type=str, required=False, default=None)
    parser.add_argument("--output_dir", type=str, required=True)
    parser.add_argument("--dataset_path", type=str, default="data/train_curated.jsonl")
    args = parser.parse_args()

    merged_model_path = merge_lora_if_needed(
        base_model_name=args.base_model,
        lora_adapter_path=args.lora_adapter,
        merged_save_path=args.output_dir,
    )

    # Setup Weights and Biases
    setup_wandb()

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=merged_model_path,
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
        output_dir=args.output_dir,
        per_device_train_batch_size=4,
        gradient_accumulation_steps=8,
        num_train_epochs=1,
        learning_rate=2e-5,
        bf16=True,
        logging_steps=1,
        save_steps=25,
        save_total_limit=2,
        report_to="wandb",
    )

    dataset = load_and_format_dataset(args.dataset_path)

    trainer = SFTTrainer(
        model=model,
        train_dataset=dataset,
        tokenizer=tokenizer,
        args=training_args,
    )

    train_segment(trainer, dataset, label="FULL", max_epochs=5)

    model.save_pretrained(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)
    print(f"[✅] Model saved to {args.output_dir}")

if __name__ == "__main__":
    main()
