# OSCAR: Optimized Structured Conversational Answers for Reasoning 

📊 Emphasizes structure, conversation, and reasoning—perfect for ConvFinQA-style multiturn datasets
🧸 Oscar is also the lovable yet misunderstood grouch from Sesame Street
---

## 🧠 Objective

Fine-tune a small, instruction-tuned LLM on structured financial reasoning tasks—such as calculating ratios and extracting numeric facts—with step-by-step supervision. Evaluate performance using both retrieval and reasoning metrics.

---

## 📦 Installation

### 1. Create Environment

```bash
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

(Or use conda if preferred)

---

### 📂 Dataset

The dataset I used is linked here [**Oscar-ConvFinQA**](https://huggingface.co/datasets/michael-sigamani/Oscar-ConvFinQA). 
It is a cleaned and Chain-of-Thought (CoT) augmented version of ConvFinQA-style examples, created using teacher LLMs and schema-based curation.

Each entry in the dataset includes:
```json
{
  "question": "...",
  "context": "...",
  "program": "...",
  "answer": "...",
  "reasoning": "...",
  "table": "..."
}
```

📌 Source: huggingface.co/datasets/michael-sigamani/Oscar-ConvFinQA

---

## 🧪 Evaluation

Evaluation is two-fold:

### 1. Retrieval Accuracy (e.g., Recall@3)

```bash
python eval/eval_retrieval_r@3.py
```

### 2. Full LangGraph Execution Accuracy

```bash
python eval/eval_langgraph.py
```

This runs the model’s predicted program over retrieved tables and compares results against gold answers.

---

## 🧬 Fine-Tuning

Fine-tune with LoRA:

```bash
python scripts/fine_tune.py --config configs/config_finetune.yaml
```

This will:
- Load a quantized model (from Hugging Face or a local GGUF file)
- Apply LoRA adapters
- Train with reasoning supervision
- Save merged model and logs to `checkpoints/`

---

## 🔍 Inference

Run inference locally using a fine-tuned checkpoint:

```bash
python scripts/run_inference.py --input example.json --checkpoint ./checkpoints/oscar-lora
```

---

## ⚙️ Configuration

All training hyperparameters are defined in `configs/config_finetune.yaml`:

```yaml
model_name_or_path: "meta-llama/Llama-2-7b-hf"
output_dir: "./checkpoints/oscar-lora"
dataset_path: "./data/curriculum_generated.jsonl"

num_train_epochs: 3
per_device_train_batch_size: 8
gradient_accumulation_steps: 2
learning_rate: 2e-4
lr_scheduler_type: "cosine"
warmup_ratio: 0.1
lora_rank: 8
lora_alpha: 16
lora_dropout: 0.05
```

---

## 📚 Citation & Credits

- Built using Hugging Face Transformers, PEFT, and LangGraph.
- Dataset adapted from ConvFinQA by TheFinAI + curriculum-generated CoT data.

---
## 🛠️ Maintainer

Michael Sigamani  
[github.com/sigamani](https://github.com/sigamani)  
Licensed under Apache 2.0
