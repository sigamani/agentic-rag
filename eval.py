import os
import uuid
import time
import csv
import dotenv
import pandas as pd
from tqdm.auto import tqdm
from datetime import datetime
from langsmith import Client
from langsmith.run_helpers import traceable
from langchain_core.messages import HumanMessage

from config import DATA_LIMIT_EVAL, GraphConfig, LANGFUSE_DATASET_NAME
from graph import graph
from utils import typed_dict_to_dict, format_prompt
from llm import llm, MODEL_NAME
from prompts import eval_prompt_template
from nodes import CHEATING_RETRIEVAL, DISABLE_GENERATION

dotenv.load_dotenv()
client = Client()

run_id = str(uuid.uuid4())
project_name = os.getenv("LANGSMITH_PROJECT")

HIGH_CORRECTNESS_THRESHOLD = 0.9

datasets = client.list_datasets()
dataset = next(ds for ds in datasets if ds.name == LANGFUSE_DATASET_NAME)
examples = list(client.list_examples(dataset_id=dataset.id))[:DATA_LIMIT_EVAL]


def relative_score(a, b, power=2):
    if a == b:
        return 1.0
    return 1 - ((abs(a - b) / max(abs(a), abs(b))) ** power)


def retrieval_precision_score(predicted, expected):
    try:
        return float(expected in predicted) / len(predicted)
    except ZeroDivisionError:
        return 0.0


def retrieval_recall_score(predicted, expected):
    return float(expected in predicted)


def correctness_score(input_q, predicted, expected):
    if DISABLE_GENERATION:
        return None

    predicted = predicted.lower().strip()
    expected = expected.lower().strip()

    if predicted == "" and expected != "":
        return 0
    if predicted == expected:
        return 1

    try:
        expected_parsed = float(
            expected.replace("%", "e-2").replace("$", "").replace(",", "")
        )
        predicted_parsed = float(
            predicted.replace("%", "e-2").replace("$", "").replace(",", "")
        )
        return relative_score(predicted_parsed, expected_parsed)
    except Exception:
        pass

    prompt = eval_prompt_template.format(
        question=input_q, actual_answer=predicted, expected_answer=expected
    )
    out = llm.invoke([HumanMessage(content=format_prompt(prompt))])
    try:
        return abs(
            float(out.content.strip().replace("<OUTPUT>", "").replace("</OUTPUT>", ""))
        )
    except:
        return None


def execution_accuracy(predicted_program, expected_answer, exec_fn):
    try:
        result = exec_fn(predicted_program)  # Safely run the DSL or Python code
        expected_val = float(
            expected_answer.replace("%", "e-2").replace("$", "").replace(",", "")
        )
        return relative_score(result, expected_val)
    except Exception as e:
        return 0.0  # or None if you want to distinguish failures


def program_accuracy(predicted_program, expected_program):
    predicted = predicted_program.strip().lower()
    expected = expected_program.strip().lower()
    return float(predicted == expected)


@traceable(name="run_eval", project_name=project_name)

def safe_eval(expr):
    try:
        return eval(expr, {"__builtins__": {}}, {})
    except Exception:
        return None

def program_accuracy_score(predicted_program, gold_program):
    return int(predicted_program.strip() == gold_program.strip())

def execution_accuracy_score(predicted_program, gold_answer):
    pred_result = safe_eval(predicted_program)
    try:
        gold_result = float(gold_answer.replace('%', '').replace("$", "").replace(",", "").strip())
    except Exception:
        gold_result = None
    return int(pred_result == gold_result if pred_result is not None and gold_result is not None else 0)
def run_eval():
    records = []

    for item in tqdm(examples):
        question = item.inputs["question"]
        expected = item.outputs["answer"]
        expected_doc_id = item.metadata["document"]["id"]

        inputs = {"messages": [HumanMessage(content=question)]}

        start = time.time()
        output = graph.invoke(
            inputs, config={"configurable": typed_dict_to_dict(GraphConfig)}
        )
        latency = time.time() - start

        answer = output["answer"]
        generation = output.get("generation", "")
        retrieved_doc_ids = [doc.metadata["id"] for doc in output.get("documents", [])]
        reranked_doc_ids = [
            doc.metadata["id"] for doc in output.get("reranked_documents", [])
        ]

        retrieval_precision = retrieval_precision_score(
            retrieved_doc_ids, expected_doc_id
        )
        retrieval_recall = retrieval_recall_score(retrieved_doc_ids, expected_doc_id)
        reranker_precision = retrieval_precision_score(
            reranked_doc_ids, expected_doc_id
        )
        reranker_recall = retrieval_recall_score(reranked_doc_ids, expected_doc_id)
        correctness = correctness_score(question, answer, expected)

        if run_id:

            records.append(
                {
                    "question": question,
                    "expected": expected,
                    "answer": answer,
                    "generation": generation,
                    "correctness": correctness,
                    "retrieval_precision": retrieval_precision,
                    "retrieval_recall": retrieval_recall,
                    "reranker_precision": reranker_precision,
                    "reranker_recall": reranker_recall,
                }
            )

    for metric, score in {
        "correctness": correctness,
        "retrieval_precision": retrieval_precision,
        "retrieval_recall": retrieval_recall,
        "reranker_precision": reranker_precision,
        "reranker_recall": reranker_recall,
    }.items():
        client.create_feedback(run_id=run_id, key=metric, score=score)

    df = pd.DataFrame(records)
    df.to_csv("eval.csv", quoting=csv.QUOTE_NONNUMERIC)
    print("~\~E Evaluation complete. Results saved to eval.csv")


    print("Average Program Accuracy:", df.get("program_accuracy", pd.Series()).mean())
    print("Average Execution Accuracy:", df.get("execution_accuracy", pd.Series()).mean())
    return {
        "inputs": {"questions": [r["question"] for r in records]},
        "outputs": {
            "summary": {
                "correctness_mean": df["correctness"].mean(),
                "high_correct_rate": (df["correctness"] > 0.9).mean(),
                "retrieval_precision_mean": df["retrieval_precision"].mean(),
                "retrieval_recall_mean": df["retrieval_recall"].mean(),
            }
        },
    }


if __name__ == "__main__":
    run_eval()
