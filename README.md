# OSCAR: ConvFinQA: Finetuning and Evaluating a Chain-of-Thought LLM on Financial QA

This repository contains the full pipeline for fine-tuning a LLaMA-style model using chain-of-thought supervision on [ConvFinQA-style](https://github.com/sigamani/ConvFinQA2) financial reasoning tasks. It includes curriculum-generated data, a LoRA fine-tuning pipeline, and LangGraph-based program execution evaluation.

---

## 📁 Project Structure
ConvFinQA3/
├── configs/                # YAML-based training config
├── data/                   # Curriculum or supervised examples
├── eval/                   # Evaluation: retrieval + reasoning accuracy
├── models/                 # Model + LoRA helpers
├── retrieval/              # Hybrid retriever logic
├── scripts/                # Training and inference scripts
├── requirements.txt
├── README.md
└── report.pdf

---

## 🧠 Objective

Fine-tune a small, instruction-tuned LLM on structured financial reasoning tasks (e.g., calculating ratios, extracting facts) with step-by-step supervision and evaluate its end-to-end performance using retrieval + reasoning metrics.

---

## 📦 Installation

### 1. Create Environment

```bash
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
(Or use conda if preferred)

⸻

## 📝 Dataset

We use curriculum_generated.jsonl – a cleaned and CoT-augmented version of ConvFinQA-style examples, created via teacher LLMs and schema-based curation.

Each entry includes:

```
  {"question": "...",
  "context": "...",
  "program": "...",
  "answer": "...",
  "reasoning": "...",
  "table": "..."}   
```
⸻

## 🧪 Evaluation

Evaluation is two-fold:

1. Retrieval Accuracy (e.g. Recall@3)

```python eval/eval_retrieval_r@3.py```

2. Full LangGraph Execution Accuracy

```python eval/eval_langgraph.py```

This runs the model’s output program over retrieved tables and compares with gold answers.

⸻

## 🧬 Fine-Tuning

✅ With LoRA
```python scripts/fine_tune.py --config configs/config_finetune.yaml```

This will:
	•	Load a quantised model (e.g. from Hugging Face or local GGUF)
	•	Apply LoRA adapters
	•	Train on the dataset with reasoning supervision
	•	Save merged model + logs to checkpoints/

⸻


## 🔍 Inference

You can run a local inference pass using the same model:
```python scripts/run_inference.py --input example.json --checkpoint ./checkpoints/oscar-lora```
## ⚙️ Config (YAML)

All hyperparameters are stored in configs/config_finetune.yaml:

```
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
⸻

📚 Citation & Credits
	•	Built using Hugging Face Transformers, PEFT, and LangGraph.
	•	Dataset adapted from ConvFinQA by TheFinAI + curriculum-generated CoT data.

⸻

🛠️ Maintainer

Michael Sigamani
github.com/sigamani
Licensed under Apache 2.0

