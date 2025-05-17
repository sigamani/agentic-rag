#!/bin/bash

set -e

# Activate virtualenv
source venv/bin/activate

# Step 1: Install requirements
pip install -r requirements-ft.txt

# Step 2: Run fine-tuning
python scripts/fine_tune.py --config configs/config_finetune.yaml

# Step 3: Run evaluation (retrieval)
echo "\n[Running Retrieval Accuracy Eval]"
python eval/eval_retrieval_r@3.py

# Step 4: Run evaluation (LangGraph accuracy)
echo "\n[Running LangGraph Execution Eval]"
python eval/eval_langgraph.py

# Step 5: Inference example
python scripts/inference.py \
  --checkpoint checkpoints/oscar-lora \
  --question "What was the net income for 2021?" \
  --context "In 2021, the company reported revenue of $200M and net income of $25M."

echo "\n‚úîè All steps completed."
