# eval_dual_retrieval_r_at3.py
import json
from data.retrieve import RelevantDocumentRetriever


def load_jsonl(filepath):
    with open(filepath, "r") as f:
        return [json.loads(line) for line in f if line.strip()]


def get_chunks(example):
    return example.get("pre_text", []) + example.get("post_text", []) + example.get("table", [])

def compute_r_at_k(method, retriever, data, k=3):
    correct = 0
    total = 0

    for example in data:
        question = example["question"]
        all_chunks = get_chunks(example)
        gold_inds = example.get("gold_inds", [])

        if method == "q2d":
            retrieved_docs = retriever.query(question, top_k=k)
        elif method == "dense":
            retrieved_docs = retriever.dense_query(question, top_k=k)
        else:
            raise ValueError("Method must be 'q2d' or 'dense'")

        retrieved_texts = [doc.page_content for doc in retrieved_docs]
        if any(all_chunks[i] in retrieved_texts for i in gold_inds):
            correct += 1
        total += 1

    recall = correct / total if total > 0 else 0.0
    print(f"[{method}] Recall@{k}: {recall:.4f} ({correct}/{total})")
    return recall

if __name__ == "__main__":
    retriever = RelevantDocumentRetriever(data_path="data/dev.json")
    data = load_jsonl("data/dev.json")

    compute_r_at_k("q2d", retriever, data, k=3)
    compute_r_at_k("dense", retriever, data, k=3)
