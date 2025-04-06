import os
import json
import time
import argparse
from datetime import datetime
from statistics import mean, quantiles

from rich import print

from main import build_rag_chain, load_and_chunk_documents, ConversationMemory
from utils.judge_llm import judge_accuracy, judge_coherence

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
        "retrieval_accuracy": len(matched_keywords) / len(expected_keywords)
        if expected_keywords
        else 0.0,
    }


def create_log_path(
    architecture,
    chunking,
    gen_model,
    embedding_model,
    prompt_strategy,
    folder="logs",
):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    subdir = f"{architecture}/{chunking}/{gen_model}_{embedding_model}/{prompt_strategy}"
    log_dir = os.path.join(folder, subdir)
    os.makedirs(log_dir, exist_ok=True)
    return os.path.join(log_dir, f"results_{timestamp}.jsonl")


def run_benchmark(
    benchmark_file,
    langsmith=False,
    evaluate=False,
    architecture="hybrid",
    chunking="semantic",
    gen_model="mistral",
    embedding_model="all-minilm",
    prompt_strategy="structured_reasoning_v1",
):
    print("[yellow]📊 Loading benchmark file...[/yellow]")
    examples = load_benchmark(benchmark_file)

    print("[yellow]📚 Loading documents and setting up chain...[/yellow]")
    documents = load_and_chunk_documents()
    chain = build_rag_chain(documents)

    latency_scores = []
    results = []

    log_path = create_log_path(
        architecture,
        chunking,
        gen_model,
        embedding_model,
        prompt_strategy,
    )

    for i, example in enumerate(examples):
        question = example["inputs"]["question"]
        conversation = example["inputs"].get("conversation", "")
        expected_keywords = example.get("metadata", {}).get("expected_keywords", [])
        golden_reference = (
            example.get("output")
            or example.get("outputs", {}).get("answer", "")
        )

        memory = ConversationMemory()
        if conversation:
            for turn in conversation.split("\n"):
                if ": " in turn:
                    role, msg = turn.split(": ", 1)
                    memory.add_turn(role, msg)
        memory.add_turn("Technician", question)

        conversation_input = {
            "question": question,
            "conversation": memory.get_history(),
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
            retrieved_context = example.get("context", "")
            if retrieved_context:
                coherence_score = judge_coherence(question, response, retrieved_context)

        print(f"[cyan]Question:[/cyan] {question}")
        print(f"[magenta]Response:[/magenta] {response}")
        print(
            f"[dim]Latency: {latency:.2f}s | Tokens: {metrics['token_count']} | Retrieval Accuracy: {metrics['retrieval_accuracy']:.2f}[/dim]"
        )
        if accuracy_score is not None:
            print(f"[bold blue]Judge Accuracy:[/bold blue] {accuracy_score:.2f}")
        if coherence_score is not None:
            print(f"[bold blue]Context Coherence:[/bold blue] {coherence_score:.2f}\n")

        results.append(
            {
                "latency": latency,
                "token_count": metrics["token_count"],
                "retrieval_accuracy": metrics["retrieval_accuracy"],
                "accuracy_score": accuracy_score,
                "coherence_score": coherence_score,
                "response": response,
                "question": question,
            }
        )
        latency_scores.append(latency)

    print("[bold yellow]📈 Benchmark Summary:[/bold yellow]")
    print(f"Mean Latency: {mean(latency_scores):.2f}s")
    print(f"P95 Latency: {quantiles(latency_scores, n=100)[94]:.2f}s")

    print(f"[green]💾 Saving benchmark log to {log_path}[/green]")
    with open(log_path, "w") as f:
        for entry in results:
            json.dump(entry, f, indent=2)
            f.write("\n\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark_file", type=str, default="data/benchmark_unified.jsonl")
    parser.add_argument("--langsmith", action="store_true", help="Enable LangSmith traces")
    parser.add_argument("--evaluate", action="store_true", help="Use judge LLM to score accuracy and coherence")
    parser.add_argument("--architecture", type=str, default="hybrid")
    parser.add_argument("--chunking", type=str, default="semantic")
    parser.add_argument("--gen_model", type=str, default="mistral")
    parser.add_argument("--embedding_model", type=str, default="all-minilm")
    parser.add_argument("--prompt_strategy", type=str, default="structured_reasoning_v1")
    args = parser.parse_args()

    run_benchmark(
        benchmark_file=args.benchmark_file,
        langsmith=args.langsmith,
        evaluate=args.evaluate,
        architecture=args.architecture,
        chunking=args.chunking,
        gen_model=args.gen_model,
        embedding_model=args.embedding_model,
        prompt_strategy=args.prompt_strategy,
    )
