import json
from pathlib import Path
from tqdm import tqdm
from retriever_1 import retriever_1
from retriever_2 import retriever_2

# --- Constants ---
TOP_K = 3
DATA_PATH = Path("data/dev.json")

# --- Load dataset ---
with open(DATA_PATH) as f:
    data = json.load(f)

# --- Evaluation ---
results = []

for example in tqdm(data):
    query = example["conversation"][-1]["content"]
    expected_chunks = example["answer"]  # list of expected DSL tokens

    retrieved_1 = retriever_1(query, k=TOP_K)
    retrieved_2 = retriever_2(query, k=TOP_K)

    def recall_at_k(retrieved, expected):
        hits = 0
        for chunk in expected:
            if any(chunk in r for r in retrieved):
                hits += 1
        return hits / len(expected) if expected else 0.0

    recall_1 = recall_at_k(retrieved_1, expected_chunks)
    recall_2 = recall_at_k(retrieved_2, expected_chunks)

    results.append({
        "id": example["id"],
        "query": query,
        "expected": expected_chunks,
        "retriever_1_r@3": recall_1,
        "retriever_2_r@3": recall_2,
    })

# --- Print summary ---
avg_r1 = sum(r["retriever_1_r@3"] for r in results) / len(results)
avg_r2 = sum(r["retriever_2_r@3"] for r in results) / len(results)
print(f"Retriever 1 avg R@3: {avg_r1:.3f}")
print(f"Retriever 2 avg R@3: {avg_r2:.3f}")

# --- Optional: Save results to file ---
with open("dual_retrieval_eval.json", "w") as f:
    json.dump(results, f, indent=2)
