import os
import json
import torch
import argparse
import wandb
from datasets import Dataset
from transformers import TrainingArguments
from trl import SFTTrainer
from unsloth import FastLanguageModel
from dotenv import load_dotenv
from peft import PeftModel
from utils.logging import setup_wandb
from utils.metrics import MetricStabiliser
from utils.llm_eval_judge import evaluate_final_answer_accuracy
from utils.curriculum_loader import load_and_split_dataset
from langsmith import Client as LangSmithClient

load_dotenv()
langsmith_client = LangSmithClient()


# --- CLI Arguments ---
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--base_model",
        type=str,
        default="models/llama2-7b_tat_lora_fp16",
        help="HF model path or local dir",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="models/llama2-7b-tat-lora-cot-fp16",
        help="Where to save finetuned model",
    )
    parser.add_argument("--data_path", type=str, default="data/train_curated.jsonl")
    return parser.parse_args()


# --- Training per Phase ---
def train_segment(segment, label, model, tokenizer, output_dir):
    print(f"\n==((====))== Training on {label.upper()} segment...")

    training_args = TrainingArguments(
        output_dir=f"{output_dir}/{label}",
        per_device_train_batch_size=4,
        gradient_accumulation_steps=8,
        num_train_epochs=5,
        learning_rate=2e-5,
        bf16=True,
        logging_steps=1,
        save_steps=25,
        save_total_limit=2,
        report_to=["wandb"],
    )

    trainer = SFTTrainer(
        model=model,
        train_dataset=segment,
        tokenizer=tokenizer,
        args=training_args,
    )

    stabiliser = MetricStabiliser(window=3, threshold=0.002)

    for epoch in range(5):
        trainer.train()
        metrics = trainer.state.log_history[-1]
        loss = metrics.get("loss", 0.0)
        accuracy = metrics.get("mean_token_accuracy", 0.0)

        # Claude-style reasoning quality eval
        claude_score = evaluate_final_answer_accuracy(segment, sample_size=100)

        stabiliser.update(loss, accuracy, claude_score)

        wandb.log(
            {
                "epoch": epoch,
                f"{label}/loss": loss,
                f"{label}/accuracy": accuracy,
                f"{label}/claude_score": claude_score,
            }
        )

        # Ensure LangSmith dataset exists
        try:
            langsmith_client.read_dataset(dataset_name="convfinqa-finetune-evals")
        except:
            langsmith_client.create_dataset(name="convfinqa-finetune-evals")

        # Log metrics to LangSmith
        langsmith_client.create_example(
            inputs={"segment_label": label},
            outputs={"loss": loss, "accuracy": accuracy, "claude_score": claude_score},
            metadata={"phase": label, "epoch": epoch},
            dataset_name="convfinqa-finetune-evals",
        )

        print(
            f"[{label.upper()}] Epoch {epoch}: Loss={loss:.4f}, Acc={accuracy:.4f}, Claude={claude_score:.4f}"
        )

        if stabiliser.should_stop():
            print(f"[__ {label.upper()}] Early stopping triggered at epoch {epoch}")
            break


# --- Main ---
def main():
    args = parse_args()
    setup_wandb()

    os.environ["UNSLOTH_RETURN_LOGITS"] = "1"

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=args.base_model,
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

    easy, medium, hard = load_and_split_dataset(args.data_path)
    curriculum = [(easy, "easy"), (medium, "medium"), (hard, "hard")]

    for segment, label in curriculum:
        train_segment(segment, label, model, tokenizer, args.output_dir)

    model.save_pretrained(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)


if __name__ == "__main__":
    main()
