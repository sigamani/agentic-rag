import os
import json
import time
import argparse
from rich import print
from statistics import mean, quantiles

from main import build_rag_chain, load_and_chunk_documents, ConversationMemory
from utils.judge_llm import judge_accuracy, judge_coherence  # scoring logic for accuracy & coherence

try:
    from langsmith import traceable
except ImportError:
    def traceable(*args, **kwargs):
        def decorator(fn):
            return fn
        return decorator

@traceable(name="Agentic RAG Benchmark Run")
def run_query(chain, conversation_input):
    return chain.invoke(conversation_input)

def load_benchmark(path):
    with open(path, "r") as f:
        return [json.loads(line) for line in f]

def measure_metrics(response, expected_keywords):
    response_lower = response.lower()
    matched_keywords = [kw for kw in expected_keywords if kw.lower() in response_lower]
    return {
        "token_count": len(response.split()),
        "retrieval_accuracy": len(matched_keywords) / len(expected_keywords) if expected_keywords else 0.0,
    }

def run_benchmark(benchmark_file, langsmith=False, evaluate=False):
    print("[yellow]📊 Loading benchmark file...[/yellow]")
    examples = load_benchmark(benchmark_file)

    print("[yellow]📚 Loading documents and setting up chain...[/yellow]")
    documents = load_and_chunk_documents()
    chain = build_rag_chain(documents)

    latency_scores = []
    results = []

    for i, example in enumerate(examples):
        question = example["inputs"]["question"]
        conversation = example["inputs"].get("conversation", "")
        expected_keywords = example.get("metadata", {}).get("expected_keywords", [])
        golden_reference = example.get("ideal", "")

        memory = ConversationMemory()
        if conversation:
            for turn in conversation.split("\n"):
                if ": " in turn:
                    role, msg = turn.split(": ", 1)
                    memory.add_turn(role, msg)
        memory.add_turn("Technician", question)

        conversation_input = {
            "question": question,
            "conversation": memory.get_history()
        }

        print(f"[bold green]⏱️ Running query {i + 1}/{len(examples)}...[/bold green]")
        start = time.time()
        response = run_query(chain, conversation_input) if langsmith else chain.invoke(conversation_input)
        end = time.time()

        latency = end - start
        metrics = measure_metrics(response, expected_keywords)

        accuracy_score = None
        coherence_score = None
        if evaluate:
            if golden_reference:
                accuracy_score = judge_accuracy(question, response, golden_reference)
            # Coherence judging only if context is retrievable
            retrieved_context = example.get("context", "")
            if retrieved_context:
                coherence_score = judge_coherence(question, response, retrieved_context)

        print(f"[cyan]Question:[/cyan] {question}")
        print(f"[magenta]Response:[/magenta] {response}")
        print(f"[dim]Latency: {latency:.2f}s | Tokens: {metrics['token_count']} | Retrieval Accuracy: {metrics['retrieval_accuracy']:.2f}[/dim]")
        if accuracy_score is not None:
            print(f"[bold blue]Judge Accuracy:[/bold blue] {accuracy_score:.2f}")
        if coherence_score is not None:
            print(f"[bold blue]Context Coherence:[/bold blue] {coherence_score:.2f}\n")

        results.append({
            "latency": latency,
            "token_count": metrics["token_count"],
            "retrieval_accuracy": metrics["retrieval_accuracy"],
            "accuracy_score": accuracy_score,
            "coherence_score": coherence_score,
            "response": response,
            "question": question,
        })
        latency_scores.append(latency)

    print("[bold yellow]📈 Benchmark Summary:[/bold yellow]")
    print(f"Mean Latency: {mean(latency_scores):.2f}s")
    print(f"P95 Latency: {quantiles(latency_scores, n=100)[94]:.2f}s")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark_file", type=str, default="data/benchmark_unified.jsonl")
    parser.add_argument("--langsmith", action="store_true", help="Enable LangSmith traces")
    parser.add_argument("--evaluate", action="store_true", help="Use judge LLM to score accuracy and coherence")
    args = parser.parse_args()

    run_benchmark(args.benchmark_file, langsmith=args.langsmith, evaluate=args.evaluate)
