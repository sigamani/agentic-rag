
import argparse
import json
import numpy as np
import re
from typing import List, Dict, Optional

# Optional wandb import
wandb = None
try:
    import wandb
except ImportError:
    pass

# Optional LangSmith import
from langsmith import Client as LangSmithClient
import os
os.environ['LANGCHAIN_API_KEY'] = os.getenv('LANGCHAIN_API_KEY', 'your-key-here')
os.environ['LANGCHAIN_PROJECT'] = os.getenv('LANGCHAIN_PROJECT', 'convfinqa-eval')


def normalize_answer(ans: str) -> Optional[float]:
    try:
        ans = ans.strip().replace(",", "").replace("$", "").replace("€", "")
        if ans.endswith('%'):
            return float(ans[:-1]) / 100
        return float(ans)
    except Exception:
        return None


def relative_error(pred: float, gold: float, tolerance: float = 1e-2) -> bool:
    if gold == 0:
        return abs(pred - gold) < tolerance
    return abs(pred - gold) / abs(gold) < tolerance


def evaluate_numeric_accuracy(predictions: List[Dict], references: List[Dict], tolerance: float = 1e-2):
    id_to_gold = {r["id"]: normalize_answer(r["answer"]) for r in references}
    correctness = []
    for pred in predictions:
        pred_id = pred["id"]
        pred_ans = normalize_answer(pred["answer"])
        gold_ans = id_to_gold.get(pred_id)
        if gold_ans is None or pred_ans is None:
            correctness.append(False)
        else:
            correctness.append(relative_error(pred_ans, gold_ans, tolerance))
    accuracy = np.mean(correctness) if correctness else 0.0
    return accuracy, correctness


def normalize_program(prog: str) -> str:
    return re.sub(r'\s+', '', prog.strip().lower())


def evaluate_program_accuracy(predictions: List[Dict], references: List[Dict]):
    id_to_gold = {r["id"]: normalize_program(r["program"]) for r in references}
    correctness = []
    for pred in predictions:
        pred_id = pred["id"]
        pred_prog = normalize_program(pred.get("program", ""))
        gold_prog = id_to_gold.get(pred_id)
        correctness.append(pred_prog == gold_prog if gold_prog else False)
    accuracy = np.mean(correctness) if correctness else 0.0
    return accuracy, correctness


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pred_file", type=str, required=True, help="Path to JSONL prediction file")
    parser.add_argument("--ref_file", type=str, required=True, help="Path to JSONL ground truth file")
    parser.add_argument("--tolerance", type=float, default=1e-2)
    parser.add_argument("--use_wandb", action="store_true")
    parser.add_argument("--use_langsmith", action="store_true")
    parser.add_argument("--project", type=str, default="convfinqa-eval")
    args = parser.parse_args()

    with open(args.pred_file) as f:
        preds = [json.loads(line) for line in f]
    with open(args.ref_file) as f:
        refs = [json.loads(line) for line in f]

    num_acc, num_correct = evaluate_numeric_accuracy(preds, refs, args.tolerance)
    prog_acc, prog_correct = evaluate_program_accuracy(preds, refs)

    print(f"Numeric Execution Accuracy: {num_acc:.3f}")
    print(f"Program Accuracy: {prog_acc:.3f}")

    if args.use_wandb and wandb:
        wandb.init(project=args.project, name="eval-run", config={"tolerance": args.tolerance})
        wandb.log({
            "numeric_execution_accuracy": num_acc,
            "program_accuracy": prog_acc
        })
        wandb.finish()

    if args.use_langsmith and LangSmithClient:
        client = LangSmithClient()
        run = client.create_run(name="eval_run", project_name=args.project, inputs={"eval_dataset": args.ref_file}, run_type="evaluation")
        client.log_metric(run.id, "numeric_execution_accuracy", num_acc)
        client.log_metric(run.id, "program_accuracy", prog_acc)
        client.end_run(run.id)


if __name__ == "__main__":
    main()
