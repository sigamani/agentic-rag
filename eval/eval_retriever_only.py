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
    retrieved_docs = retriever.query(question, top_k=k)
    retrieved_texts = [doc.page_content for doc in retrieved_docs]

    try:
        return float(expected in retrieved_texts) / len(retrieved_texts)
    except ZeroDivisionError:
        return 0.0

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dataset", type=str, default="TheFinAI/CONVFINQA_train", help="Hugging Face dataset path"
    )
    parser.add_argument("--subset", type=str, default="dev", help="Subset to evaluate on")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    dataset = load_dataset(args.dataset, split=args.subset)

    print("Running Evaluation on:", args.dataset, args.subset)

    # Metric 1: Correctness
    run_evaluation(
        dataset,
        lambda ex: correctness_score(load_predicted_output(ex), load_expected_output(ex)),
        "Correctness",
    )

    # Metric 2: Execution Accuracy
    run_evaluation(
        dataset,
        lambda ex: execution_accuracy_score(load_predicted_output(ex), load_expected_output(ex)),
        "Execution Accuracy",
    )

    # Metric 3: Semantic Equivalence
    run_evaluation(
        dataset,
        lambda ex: semantic_equivalence_score(load_predicted_output(ex), load_expected_output(ex)),
        "Semantic Equivalence",
    )

    # Metric 4: Retrieval Precision (Numeric+BGE)
    run_evaluation(
        dataset,
        lambda ex: retrieval_precision_score(
            ex["inputs"]["question"],
            ex["inputs"]["chunks"],
            ex["metadata"]["expected_sources"][0],
            k=3,
        ),
        "Retrieval Precision (Numeric+BGE)",
    )
