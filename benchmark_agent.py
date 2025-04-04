import time
import argparse
import wandb
from run_agent import load_and_chunk_documents, build_rag_chain, ConversationMemory

def benchmark(query: str, hardware: str):
    wandb.init(project="agentic-rag-benchmark", config={"hardware": hardware})
    documents = load_and_chunk_documents()
    chain = build_rag_chain(documents)
    memory = ConversationMemory()
    memory.add_turn("Technician", query)
    conversation_input = {
        "question": query,
        "conversation": memory.get_history(),
    }

    start_time = time.time()
    response = chain.invoke(conversation_input)
    end_time = time.time()

    latency = end_time - start_time
    response_length = len(response.split())
    throughput = response_length / latency if latency > 0 else 0

    print(f"🧠 {response}")
    print(f"⏱️ Latency: {latency:.2f}s | Tokens: {response_length} | Throughput: {throughput:.2f} tokens/sec")

    wandb.log({
        "query": query,
        "latency_sec": latency,
        "response_length": response_length,
        "throughput_tps": throughput
    })

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", type=str, required=True, help="Technician query to benchmark")
    parser.add_argument("--hardware", type=str, required=True, help="Hardware identifier (e.g. macbook-m2)")
    args = parser.parse_args()
    benchmark(args.query, args.hardware)

if __name__ == "__main__":
    main()

