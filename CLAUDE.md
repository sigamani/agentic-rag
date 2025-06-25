# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a ConvFinQA RAG (Retrieval-Augmented Generation) pipeline that fine-tunes small instruction-tuned LLMs on structured financial reasoning tasks. The system performs step-by-step financial calculations and table reasoning with retrieval and generation components.

## Key Architecture Components

### Core Pipeline (LangGraph)
- **LangGraph Workflow**: Multi-node graph in `langgraph/` with nodes for question extraction, query generation, retrieval, generation, and answer extraction
- **State Management**: Centralized state handling in `langgraph/state.py` for the AgentState flow
- **Node Operations**: Individual processing nodes in `langgraph/nodes.py` for each pipeline step

### Model Infrastructure
- **LLM Integration**: Uses Ollama with fine-tuned models (default: `hf.co/mradermacher/tat-llm-7b-fft-i1-GGUF:Q4_K_M`)
- **Fine-tuning Pipeline**: LoRA-based fine-tuning with curriculum learning (easy → medium → hard difficulty progression)
- **Model Architecture**: Unsloth + transformers stack with 4-bit quantization and LoRA adapters

### Data Flow
- **Dataset**: Oscar-ConvFinQA from HuggingFace (`michael-sigamani/Oscar-ConvFinQA`) with CoT reasoning
- **Retrieval**: Dual retrieval system (q2d and dense methods) for finding relevant financial documents
- **Evaluation**: Two-tier evaluation (retrieval accuracy + full pipeline execution)

## Development Commands

### Environment Setup
```bash
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Training & Fine-tuning
```bash
# Fine-tune with curriculum learning
python scripts/fine-tune.py --base_model michael-sigamani/llama2-7b-tat-lora-fp16 --output_dir models/llama2-7b-tat-lora-cot-fp16 --data_path data/train_curated.jsonl

# Alternative fine-tuning (simpler)
python scripts/fine_tune.py --config configs/config_finetune.yaml
```

### Evaluation
```bash
# Retrieval accuracy evaluation (Recall@3)
python eval/eval_retrieval_r@3.py

# Full LangGraph pipeline evaluation
python eval/eval_langgraph.py

# Retriever-only evaluation
python eval/eval_retriever_only.py
```

### Inference
```bash
# Run inference with fine-tuned checkpoint
python scripts/inference.py --checkpoint ./checkpoints/oscar-lora --question "your question" --context "your context"

# Run full pipeline
python run_pipeline.py
```

### Data Processing
```bash
# Create dataset
python data/create_dataset.py

# Create database
python data/create_db.py

# Parse tables with LLM
python data/llm_parse_table.py
```

## Key Configuration Files

- `configs/fine_tuning.yaml`: Training hyperparameters and model configuration
- `requirements.txt`: Python dependencies with CUDA 11.7 support
- Data files expected in `data/` directory (JSONL format)

## Important Notes

- Models use CUDA 11.7 with PyTorch 1.13.1
- Fine-tuning uses curriculum learning with 3 difficulty levels
- Evaluation includes both retrieval metrics and end-to-end accuracy
- LangSmith integration for experiment tracking
- Wandb integration for training monitoring
- Uses Unsloth for efficient fine-tuning with LoRA adapters

## Known Issues and Fixes Applied

### Code Quality Issues (Fixed)
- **Undefined Variables**: Fixed `flush_interval` in `data/llm_parse_table.py:75`
- **Git Merge Conflicts**: Cleaned up merge conflict markers in `utils/prompts.py`
- **Commented References**: Removed broken `langfuse_handler` reference in `langgraph/graph.py:68`

### Data Processing Issues
- **Numerical Suffixes**: Created `utils/data_preprocessing.py` with proper handling of M/B/K suffixes
- **Currency Symbols**: Added proper normalization for $, %, and other financial symbols
- **Value Extraction**: Implemented `normalize_financial_value()` function for accurate financial data processing

### Evaluation Issues
- **Misaligned Metrics**: Current evaluations focus on retrieval accuracy (R@3) rather than fine-tuning objectives
- **Missing Integration**: Evaluations are not properly integrated with the fine-tuned model outputs
- **Recommendation**: Use `evaluator_full.py` for proper numeric and program accuracy evaluation

### Documentation Issues
- **Broken Citations**: report.pdf has all citations showing as `[?]` - requires LaTeX source files to fix
- **Missing Bibliography**: References section is empty, causing citation resolution failures

## Usage Recommendations

1. **Before Training**: Use the new data preprocessing utilities to properly normalize financial values
2. **During Evaluation**: Focus on numeric execution accuracy rather than just retrieval metrics
3. **For Production**: Ensure all undefined variables are properly initialized before deployment