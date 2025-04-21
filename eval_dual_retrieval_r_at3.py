# eval_dual_retrieval_r_at3.py
import json
from retrieve import RelevantDocumentRetriever

def load_gold_data(file_path):
    with open(file_path, "r") as f:
        return json.load(f)

def compute_r_at_k(method, retriever, data, k=3):
    correct = 0
    total = 0

    for example in data:
        question = example["qa"]["question"]
        expected_chunks = example["evidence"]  # list of expected substrings

        if method == "q2d":
            retrieved_docs = retriever.query(question, top_k=k)
        elif method == "dense":
            retrieved_docs = retriever.dense_query(question, top_k=k)
        else:
            raise ValueError("Method must be 'q2d' or 'dense'")

        retrieved_texts = [doc.page_content for doc in retrieved_docs]
        if any(gold in text for gold in expected_chunks for text in retrieved_texts):
            correct += 1
        total += 1

    recall = correct / total if total > 0 else 0.0
    print(f"[{method}] Recall@{k}: {recall:.4f} ({correct}/{total})")
    return recall

if __name__ == "__main__":
    retriever = RelevantDocumentRetriever(data_path="data/convfinqa_dev.json")
    data = load_gold_data("data/convfinqa_dev.json")

    compute_r_at_k("q2d", retriever, data, k=3)
    compute_r_at_k("dense", retriever, data, k=3)
