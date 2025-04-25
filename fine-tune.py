import os
import json
import torch
import wandb
from datasets import Dataset
from transformers import TrainingArguments, AutoModelForCausalLM, AutoTokenizer
from trl import SFTTrainer
from dotenv import load_dotenv
from utils.logging import setup_wandb
from utils.metrics import MetricStabiliser
from utils.llm_eval_judge import evaluate_final_answer_accuracy, push_segment_to_langsmith
from utils.curriculum_loader import load_and_split_dataset
from langsmith import Client as LangSmithClient
from huggingface_hub import HfApi, login

load_dotenv()
langsmith_client = LangSmithClient()

# --- Constants ---
BASE_MODEL = "michael-sigamani/llama2-7b-tat-convfinqa-fp16"
OUTPUT_DIR = "models/llama2-7b-tat-convfinqa-curriculum-cot-fp16"
DATA_PATH = "data/train_curated.jsonl"
LANGSMITH_DATASET = "convfinqa-cot-train2"
HF_REPO_ID = "michael-sigamani/llama2-7b-tat-convfinqa-Curriculum-CoT-fp16"

# --- Training per Phase ---
def train_segment(segment, label, model, tokenizer):
    print(f"\n==((====))== Training on {label.upper()} segment...")

    training_args = TrainingArguments(
        output_dir=f"{OUTPUT_DIR}/{label}",
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

        claude_score, _ = evaluate_final_answer_accuracy(segment, sample_size=100)

        # Push evaluated examples and Claude score to LangSmith
        push_segment_to_langsmith(segment, label, dataset_name=LANGSMITH_DATASET)

        langsmith_client.create_example(
            inputs={"segment_label": label},
            outputs={"claude_score": claude_score},
            metadata={"phase": label, "epoch": epoch},
            dataset_name=LANGSMITH_DATASET,
        )

        wandb.log(
            {
                "epoch": epoch,
                f"{label}/loss": loss,
                f"{label}/accuracy": accuracy,
                f"{label}/claude_score": claude_score,
            }
        )

        print(
            f"[{label.upper()}] Epoch {epoch}: Loss={loss:.4f}, Acc={accuracy:.4f}, Claude={claude_score:.4f}"
        )

        if stabiliser.should_stop():
            print(f"[__ {label.upper()}] Early stopping triggered at epoch {epoch}")
            break

# --- Main ---
def main():
    setup_wandb()

    print("Loading base model...")
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True
    )

    easy, medium, hard = load_and_split_dataset(DATA_PATH)
    curriculum = [(easy, "easy"), (medium, "medium"), (hard, "hard")]

    for segment, label in curriculum:
        train_segment(segment, label, model, tokenizer)

    model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)

    # --- Upload merged model to Hugging Face ---
    print(f"Uploading {OUTPUT_DIR} to Hugging Face Hub: {HF_REPO_ID}")
    login(token=os.environ.get("HF_TOKEN"))
    api = HfApi()
    api.upload_folder(
        folder_path=OUTPUT_DIR,
        repo_id=HF_REPO_ID,
        repo_type="model",
        commit_message="Upload final fine-tuned ConvFinQA Curriculum CoT model",
        private=False,
    )

    print("✅ Upload complete!")

if __name__ == "__main__":
    main()
