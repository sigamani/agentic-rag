import os
import json
import torch
import argparse
from dotenv import load_dotenv
from transformers import TrainingArguments
from trl import SFTTrainer
from unsloth import FastLanguageModel
from datasets import Dataset
from utils.curriculum_loader import load_and_split_dataset
from utils.llm_eval_judge import evaluate_final_answer_accuracy_claude as evaluate_final_answer_accuracy
from utils.logging import setup_wandb
from utils.metrics import MetricStabiliser


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_path", type=str, required=True, help="Path to base model (e.g., ./merged_tat_llm_fp16)")
    parser.add_argument("--output_path", type=str, default="tat_llm_convfinqa_cot", help="Directory to save model")
    args = parser.parse_args()

    load_dotenv()
    setup_wandb()

    # === Load and Split Dataset ===
    data_path = "../data/train_curated.jsonl"
    easy, medium, hard = load_and_split_dataset(data_path)

    # === Load Base Model ===
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=args.model_path,
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

    os.environ["UNSLOTH_RETURN_LOGITS"] = "1"

    training_args = TrainingArguments(
        output_dir=args.output_path,
        per_device_train_batch_size=4,
        gradient_accumulation_steps=8,
        num_train_epochs=1,
        learning_rate=2e-5,
        bf16=True,
        logging_steps=1,
        save_steps=25,
        save_total_limit=2,
        report_to=["wandb"],
    )

    def train_segment(segment, label):
        print(f"\n==((====))== Training on {label.upper()} segment...")
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
            claude_score = evaluate_final_answer_accuracy(segment, sample_size=100)

            stabiliser.update(loss, accuracy, claude_score)

            print(
                f"[{label.upper()}] Epoch {epoch}: Loss={loss:.4f}, Acc={accuracy:.4f}, Claude={claude_score:.4f}"
            )

            if stabiliser.should_stop():
                print(f"[Stopping Early] Stable metrics on {label.upper()} at epoch {epoch}")
                break

    train_segment(easy, "easy")
    train_segment(medium, "medium")
    train_segment(hard, "hard")

    model.save_pretrained(args.output_path)
    tokenizer.save_pretrained(args.output_path)


if __name__ == "__main__":
    main()
