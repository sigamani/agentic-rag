import json
import argparse
from datasets import load_dataset
from evaluator import (
    correctness_score,
    execution_accuracy_score,
    semantic_equivalence_score,
)
from retrieve import RelevantDocumentRetriever

# New: use updated retriever with BGE + numeric filtering
retriever = RelevantDocumentRetriever(data_path="data/convfinqa_dev.json")

def load_expected_output(example):
    return example["outputs"]["answer"]

def load_predicted_output(example):
    return example["outputs"].get("prediction", "")

def run_evaluation(dataset, metric_fn, metric_name):
    results = []
    for example in dataset:
        try:
            result = metric_fn(example)
            results.append(result)
        except Exception as e:
            print(f"[{metric_name}] Error evaluating example: {e}")
            results.append(0.0)
    avg_score = sum(results) / len(results)
    print(f"{metric_name}: {avg_score:.4f}")
    return avg_score

def retrieval_precision_score(question, chunks, expected, k=3):
   
