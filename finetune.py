import os
import json
import torch
from transformers import TrainingArguments
from trl import SFTTrainer
from unsloth import FastLanguageModel
from datasets import Dataset
from llm_eval_judge import evaluate_final_answer_accuracy_claude as evaluate_final_answer_accuracy

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
