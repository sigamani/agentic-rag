import os
import json
import torch
from datasets import Dataset
from transformers import TrainingArguments
from trl import SFTTrainer
from unsloth import FastLanguageModel
from copy import deepcopy
import random

import os
import json
import openai  # You can swap with Anthropic Claude later

# Set API key from environment variable
openai.api_key = os.environ.get("OPENAI_API_KEY")  # or CLAUDE_API_KEY if swapping to Anthropic

def score_flexible_final_answer(reasoning: str, final_answer: str) -> float:
    """
    Uses an LLM (e.g., GPT-4 or Claude) to judge whether the final answer is acceptable,
    even if not numerically exact — as long as the reasoning shows a clear path to it.
    """

    prompt = f"""
You are an expert tutor evaluating a student's financial reasoning.

They were asked to solve a problem and gave the following explanation and final answer.
Please judge with empathy — this student is learning, so small errors in formatting or rounding are acceptable.

Your job is to score how well their reasoning leads to the final answer, and whether that answer is acceptably close to the correct result.

Use the following rubric:
- 1.0 = Final answer is correct or acceptably close; reasoning is sound and complete.
- 0.5 = Reasoning is on the right track, but unclear or has small logical flaws; final answer is somewhat plausible.
- 0.0 = Final answer is clearly wrong or missing; reasoning is flawed or incomplete.

Be lenient on rounding, units (e.g. millions vs. dollars), formatting (e.g. '14%' vs. '0.14'), and slight deviations.
You are a human evaluator using good judgement, not a strict grader.

Respond with just the numeric score: 1.0, 0.5, or 0.0 — no explanation.

---

Reasoning:
{reasoning}

Final Answer (as claimed by the student):
{final_answer}

Score:
"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",  # Swap for Claude-compatible if needed
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        score_text = response['choices'][0]['message']['content'].strip()
        return float(score_text)
    except Exception as e:
        print(f"[⚠️ LLM Eval Error] {e}")
        return 0.0


def evaluate_final_answer_accuracy(dataset, sample_size=100):
    """Evaluates model final answer quality on a subset using a discretionary judge."""
    print("[🔍 Final Answer Evaluation] Using LLM judge to assess student output...")
    subset = dataset.select(range(min(sample_size, len(dataset))))
    results = []
    for ex in subset:
        reasoning = ex.get("output", "")
        final = ex.get("Final Answer", "")
        score = score_flexible_final_answer(reasoning, str(final))
        results.append(score)

    avg_score = sum(results) / len(results) if results else 0.0
    print(f"[✅ Final Answer Score]: {avg_score:.3f} over {len(results)} examples")
    return avg_score

import os
import json
import torch
from transformers import TrainingArguments
from trl import SFTTrainer
from unsloth import FastLanguageModel
from datasets import Dataset
from llm_eval_judge import evaluate_final_answer_accuracy

# === Load and Format ===
def load_and_format_dataset(filepath):
    with open(filepath, "r") as f:
        raw_data = [json.loads(line) for line in f if line.strip()]

    def format_with_cot(example):
        final_answer_raw = example.get("Final Answer", "")
        try:
            final_answer_float = float(str(final_answer_raw).replace(",", "").replace("%", "e-2").replace("$", "").strip())
        except:
            final_answer_float = None  # fallback if conversion fails

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
            "Final Answer": final_answer_float
        }

    formatted = list(map(format_with_cot, raw_data))
    return Dataset.from_list(formatted)
    

def merge_fields(example):
    example["text"] = f"""
### Instruction:
{example['instruction']}

### Input:
{example['input']}

### Response:
{example['output']}
    """
    return example

# === Load Curriculum Segments ===
data_path = "data/train_curated.jsonl"
dataset = load_and_format_dataset(data_path)

# Sort by program length
dataset = dataset.filter(lambda ex: "Program" in ex and ex["Program"])
dataset = dataset.sort("Program", reverse=False, key=lambda x: len(x["Program"]))

n = len(dataset)
easy = dataset.select(range(int(0.33 * n))).map(merge_fields)
medium = dataset.select(range(int(0.33 * n), int(0.66 * n))).map(merge_fields)
hard = dataset.select(range(int(0.66 * n), n)).map(merge_fields)

# === Load Model ===
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

os.environ['UNSLOTH_RETURN_LOGITS'] = '1'

# === Training Phases ===
def train_segment(segment, label):
    print(f"\n==((====))== Training on {label.upper()} segment...")
    trainer = SFTTrainer(
        model=model,
        train_dataset=segment,
        tokenizer=tokenizer,
        args=training_args,
    )
    trainer.train()
    evaluate_final_answer_accuracy(segment, sample_size=100)

train_segment(easy, "easy")
train_segment(medium, "medium")
train_segment(hard, "hard")

# === Save ===
model.save_pretrained("tat_llm_convfinqa_cot")
tokenizer.save_pretrained("tat_llm_convfinqa_cot")
