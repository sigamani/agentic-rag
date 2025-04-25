import argparse
import os
from transformers import TrainingArguments
from trl import SFTTrainer
from unsloth import FastLanguageModel
from curriculum_loader import load_and_split_dataset
from llm_eval_judge import evaluate_final_answer_accuracy_claude as evaluate_final_answer_accuracy
from utils.logging import setup_wandb
from utils.metrics import MetricStabiliser


def train_curriculum_model(base_model_path, output_dir):
    os.environ["UNSLOTH_RETURN_LOGITS"] = "1"

    # Load datasets
    data_path = "../data/train_curated.jsonl"
    easy, medium, hard = load_and_split_dataset(data_path)
    datasets = {"easy": easy, "medium": medium, "hard": hard}

    # Load model
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=base_model_path,
        max_seq_length=4096,
        dtype="bfloat16",
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

    best_claude_score = 0.0

    # Curriculum
    curriculum = [("easy", 5), ("medium", 5), ("hard", 5)]
    for phase, max_epochs in curriculum:
        print(f"\n======== Training on {phase.upper()} segment...")
        training_args = TrainingArguments(
            output_dir=f"{output_dir}_{phase}",
            per_device_train_batch_size=4,
            gradient_accumulation_steps=8,
            num_train_epochs=1,
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

        stabiliser = MetricStabiliser(window=3, threshold=0.002)

        for epoch in range(max_epochs):
            trainer.train()
            metrics = trainer.state.log_history[-1]
            loss = metrics.get("loss", 0.0)
            accuracy = metrics.get("mean_token_accuracy", 0.0)
            claude_score = evaluate_final_answer_accuracy(datasets[phase], sample_size=100)

            stabiliser.update(loss, accuracy, claude_score)

            print(f"[{phase.upper()}] Epoch {epoch}: Loss={loss:.4f}, Acc={accuracy:.4f}, Claude={claude_score:.4f}")

            if claude_score > best_claude_score:
                print("[__ New Best Claude Score] Saving to Hugging Face Hub...")
                model.save_pretrained(output_dir)
                tokenizer.save_pretrained(output_dir)
                best_claude_score = claude_score

            if stabiliser.should_stop():
                print(f"[Stopping Early] Stable metrics on {phase.upper()} at epoch {epoch}")
                break


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base_model", type=str, required=True, help="Path to base model (e.g. ./merged_tat_llm_fp16)")
    parser.add_argument("--output_dir", type=str, required=True, help="Directory to save final model")
    args = parser.parse_args()

    setup_wandb("pr-convfinqa-01")
    train_curriculum_model(args.base_model, args.output_dir)
