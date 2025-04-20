from datetime import datetime
import csv
import time
import dotenv
import pandas as pd
from tqdm.auto import tqdm
from langsmith import Client
from langsmith import traceable
from langchain_core.messages import HumanMessage
from config import DATA_LIMIT_EVAL, LANGFUSE_DATASET_NAME, GraphConfig
from utils import typed_dict_to_dict, format_prompt
from prompts import eval_prompt_template
from llm import llm, MODEL_NAME
from nodes import CHEATING_RETRIEVAL, DISABLE_GENERATION
from graph import graph

dotenv.load_dotenv()
client = Client()
datasets = client.list_datasets()
dataset = next((ds for ds in datasets if ds.name == LANGFUSE_DATASET_NAME), None)
if dataset is None:
    raise ValueError(f"Dataset '{LANGFUSE_DATASET_NAME}' not found in LangSmith")
examples = list(client.list_examples(dataset_id=dataset.id))[:DATA_LIMIT_EVAL]

HIGH_CORRECTNESS_THRESHOLD = 0.9

def relative_score(a, b, power=2) -> float:
    if a == b:
        return 1.0
    return 1 - ((abs(a - b) / max(abs(a), abs(b))) ** power)

def retrieval_precision_score(predicted: list[str], expected: str) -> float:
    try:
        return float(expected in predicted) / len(predicted)
    except ZeroDivisionError:
        return 0

def retrieval_recall_score(predicted: list[str], expected: str) -> float:
    return float(expected in predicted)

def correctness_score(input: str, predicted: str, expected: str):
    if DISABLE_GENERATION:
        return None

    predicted = predicted.lower().strip()
    expected = expected.lower().strip()

    if predicted == "" and expected != "":
        return 0
    if predicted != "" and expected == "":
        return None
    if predicted == expected:
        return 1

    try:
        expected_parsed = float(expected.replace('%', 'e-2').replace("$", "").replace(",", "").replace(" ", ""))
        predicted_parsed = float(predicted.replace('%', 'e-2').replace("$", "").replace(",", "").replace(" ", ""))
        return relative_score(predicted_parsed, expected_parsed)
    except Exception:
        pass

    prompt = eval_prompt_template.format(question=input, actual_answer=predicted, expected_answer=expected)
    out = llm.invoke([HumanMessage(content=format_prompt(prompt))])
    try:
        return abs(float(out.content.strip().replace("<OUTPUT>", "").replace("</OUTPUT>", "")))
    except:
        return None

def get_doc_selection_display(retrieved_doc_ids: list[str], expected_doc_id: str) -> str:
    display = ", ".join([f"+{doc}" if doc == expected_doc_id else doc for doc in retrieved_doc_ids])
    if expected_doc_id not in retrieved_doc_ids:
        display += f", -{expected_doc_id}"
    return display

@traceable(name="rag-eval")
def run_eval():
    answer_correctness_scores = []
    retrieval_precision_scores = []
    retrieval_recall_scores = []
    reranker_precision_scores = []
    reranker_recall_scores = []
    latencies = []
    out = []

    for item in tqdm(examples):
        inputs = {
            "messages": [
                HumanMessage(content=item.inputs["question"])
            ]
        }

        start = time.time()
        output = graph.invoke(inputs, config={"configurable": typed_dict_to_dict(GraphConfig)})
        latency = time.time() - start
        latencies.append(latency)

        question = item.inputs["question"]
        expected_answer = item.outputs["answer"]
        answer = output['answer']
        generation = output['generation']

        retrieved_doc_ids = [doc.metadata['id'] for doc in output['documents']]
        expected_doc_id = item.metadata['document']['id']

        reranked_doc_ids = [doc.metadata['id'] for doc in output['reranked_documents']]

        retrieval_precision = retrieval_precision_score(retrieved_doc_ids, expected_doc_id)
        retrieval_recall = retrieval_recall_score(retrieved_doc_ids, expected_doc_id)
        reranker_precision = retrieval_precision_score(reranked_doc_ids, expected_doc_id)
        reranker_recall = retrieval_recall_score(reranked_doc_ids, expected_doc_id)

        correctness = correctness_score(question, answer, expected_answer)

        print("=" * 50)
        print("Question:", question)
        print("Answer:", answer)
        print("Expected:", expected_answer)
        print("Correctness:", correctness)
        print("Documents:", retrieved_doc_ids)
        print("Reranked:", reranked_doc_ids)
        print("Output State:", output)

        out.append({
            "question": question,
            "answer": answer,
            "generation": generation,
            "expected_answer": expected_answer,
            "correctness": correctness,
            "retrieval_precision": retrieval_precision,
            "retrieval_recall": retrieval_recall,
            "reranker_precision": reranker_precision,
            "reranker_recall": reranker_recall,
            "prompt": output.get("prompt", ""),
            "latency": latency,
        })

    out_df = pd.DataFrame.from_records(out)
    out_df.to_csv("eval.csv", quoting=csv.QUOTE_NONNUMERIC)

    correct_scores = [c for c in answer_correctness_scores if c is not None]
    if correct_scores:
        mean_correctness = sum(correct_scores) / len(correct_scores)
        high_correctness_rate = sum(c > HIGH_CORRECTNESS_THRESHOLD for c in correct_scores) / len(correct_scores)
        print(f"Average Correctness: {mean_correctness:.2%}")
        print(f"High Correctness Rate: {high_correctness_rate:.2%}")

    print(f"Mean Retrieval Precision: {sum(retrieval_precision_scores) / len(retrieval_precision_scores):.2%}")
    print(f"Mean Retrieval Recall: {sum(retrieval_recall_scores) / len(retrieval_recall_scores):.2%}")
    print(f"Mean Reranker Precision: {sum(reranker_precision_scores) / len(reranker_precision_scores):.2%}")
    print(f"Mean Reranker Recall: {sum(reranker_recall_scores) / len(reranker_recall_scores):.2%}")
    print(f"Mean Latency: {sum(latencies) / len(latencies):.2f}s")

if __name__ == "__main__":
    run_eval()
