import os
import json
import torch
from transformers import TrainingArguments
from trl import SFTTrainer
from unsloth import FastLanguageModel
from datasets import Dataset
from llm_eval_judge import evaluate_final_answer_accuracy_claude as evaluate_final_answer_accuracy
from dotenv import load_dotenv

# Metric stabilisation for early stopping
class MetricStabiliser:
    def __init__(self, window=3, threshold=0.002):
        self.history = {
            "loss": [],
            "accuracy": [],
            "claude_score": [],
        }
        self.window = window
        self.threshold = threshold

    def update(self, loss, accuracy, claude_score):
        self.history["loss"].append(loss)
        self.history["accuracy"].append(accuracy)
        self.history["claude_score"].append(claude_score)

    def _is_stable(self, values):
        if len(values) < self.window:
            return False
        recent = values[-self.window:]
        return max(recent) - min(recent) < self.threshold

    def should_stop(self):
        return all(
            [
                self._is_stable(self.history["loss"]),
                self._is_stable(self.history["accuracy"]),
                self._is_stable(self.history["claude_score"]),
            ]
        )

load_dotenv()

# === Load and Format Dataset ===
def load_and_format_dataset(filepath):
    with open(filepath, "r") as f:
        raw_data = [json.loads(line) for line in f if line.strip()]

    def format_with_cot(example):
        final_answer_raw = example.get("Final Answer", "")
        try:
            final_answer_float = float(
                str(final_answer_raw).replace(",", "").replace("%", "e-2").replace("$", "").strip()
            )
        except:
            final_answer_float = None

        reasoning_template = f"""
        You are a financial reasoning assistant.

        Given a question based on a financial report (with pre-text, post-text, and table snippets), think step-by-step to identify the right values and apply the correct calculation.

        Always follow this format:

        Step 1: Rephrase the question for clarity.
        Step 2: Identify key values from the table or context.
        Step 3: Apply the correct operation (e.g., subtraction, percentage change).
        Step 4: Compute the result.
        Final Answer: <answer as a single number in float format>

        Question: {example['input']}

        Step 1: Let's rephrase the question.
        Step 2: We need to find relevant values.
        Step 3: We apply: {example.get('Program', '')}
        Step 4: Result of calculation.
        Final Answer: {final_answer_raw}
        """

        return {
            "instruction": example["instruction"],
            "input": example["input"],
            "output": reasoning_template,
            "Final Answer": final_answer_float,
        }

    formatted = list(map(format_with_cot, raw_data))
    return Dataset.from_list(formatted)

# === Load and Split Dataset ===
from curriculum_loader import load_and_split_dataset

data_path = "../data/train_curated.jsonl"
easy, medium, hard = load_and_split_dataset(data_path)

# === Load Model ===
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="../models/merged_tat_llm_fp16",
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
    output_dir="tat_llm_convfinqa_cot",
    per_device_train_batch_size=4,
    gradient_accumulation_steps=8,
    num_train_epochs=1,
    learning_rate=2e-5,
    bf16=True,
    logging_steps=1,
    save_steps=25,
    save_total_limit=2,
)

os.environ["UNSLOTH_RETURN_LOGITS"] = "1"

# === Train ===
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

        print(f"[{label.upper()}] Epoch {epoch}: Loss={loss:.4f}, Accuracy={accuracy:.4f}, Claude={claude_score:.4f}")
        if stabiliser.should_stop():
            print(f"[__ {label.upper()}] Early stopping triggered at epoch {epoch}")
            break

train_segment(easy, "easy")
train_segment(medium, "medium")
train_segment(hard, "hard")

# === Save Final Model ===
model.save_pretrained("tat_llm_convfinqa_curriculum")
tokenizer.save_pretrained("tat_llm_convfinqa_curriculum")
