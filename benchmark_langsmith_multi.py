import time
from langsmith import Client
from run_agent import build_rag_chain, load_and_chunk_documents, ConversationMemory

client = Client()
dataset_name = "agentic-troubleshooting"

print(f"[INFO] Starting multi-turn evaluation for dataset: {dataset_name}")
examples = client.list_examples(dataset_name=dataset_name)

# Load RAG pipeline once
documents = load_and_chunk_documents()
chain = build_rag_chain(documents)

results = []

for example in examples:
    question = example.inputs["question"]
    conversation = example.inputs["conversation"]

    memory = ConversationMemory()
    for turn in conversation.split("\n"):
        if turn.strip():
            role, msg = turn.split(":", 1)
            memory.add_turn(role.strip(), msg.strip())
    memory.add_turn("Technician", question)

    inputs = {
        "question": question,
        "conversation": memory.get_history(),
    }

    print(f"\n[User] {question}")
    start = time.time()
    try:
        response = chain.invoke(inputs)
        duration = time.time() - start
        print(f"[Assistant] {response}")
        print(f"[Time] {duration:.2f}s")

        results.append({
            "question": question,
            "response": response,
            "expected_keywords": example.metadata.get("expected_keywords", []),
            "expected_sources": example.metadata.get("expected_sources", []),
            "latency_s": duration
        })

    except Exception as e:
        print(f"[ERROR] Failed to process: {e}")
        results.append({
            "question": question,
            "response": None,
            "error": str(e),
        })

# Optional: save results to a file
with open("multi_eval_results.jsonl", "w") as f:
    for r in results:
        f.write(f"{r}\n")

print("\n✅ Evaluation run complete.")
