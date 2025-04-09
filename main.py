import argparse
import json
import time
import logging
import asyncio
from rich import print

from constants import BENCHMARK_FILE, CHAT_MODEL, EMBED_MODEL, TEXT_FILE
from create_vector_store import create_vector_store, vector_store_exists
from parser import chunk_txt_to_docs
from retrieval import get_retriever
from rag_chain import build_chain
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnableMap
from langchain.memory import ConversationBufferMemory

from langchain_chroma import Chroma  
from judge_llm import (
    judge_accuracy,
    judge_coherence,
    #judge_retrieval_quality,
)

logging.basicConfig(level=logging.INFO)

def trim_response(response: str, max_tokens: int = 30) -> str:
    if "### Final Response" in response:
        response = response.split("### Final Response", 1)[-1]
    return " ".join(response.split()[:max_tokens]) + " ..."

def format_timings(t0, t1, t2) -> str:
    return f"🧠 Retrieval: {t1 - t0:.2f}s | 🗣️ Chat: {t2 - t1:.2f}s | ⏱️ Total: {t2 - t0:.2f}s"

def run_chat(chain, retriever, verbose=False):
    print("\n💬 RAG Chat Interface (type 'exit' to quit)\n")
    memory = ConversationBufferMemory(return_messages=False)

    while True:
        try:
            query = input("Technician: ")
            if query.lower() in ["exit", "quit"]:
                print("👋 Goodbye!")
                break

            t0 = time.time()
            context = retriever.get_relevant_documents(query)
            t1 = time.time()
            response = chain.invoke({
                "question": query,
                "conversation": memory.buffer,
                "context": context,
            })
            t2 = time.time()

            output = response if verbose else trim_response(response)
            print(f"\nAI Assistant: {output}")
            print(format_timings(t0, t1, t2) + "\n")

            memory.save_context({"input": query}, {"output": response})

        except KeyboardInterrupt:
            print("\n👋 Exiting chat.")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

async def run_benchmark(chain, retriever):
    import jsonlines
    from pathlib import Path

    benchmark_path = Path("data/benchmark_unified.jsonl")
    if not benchmark_path.exists():
        raise FileNotFoundError("Benchmark file not found.")

    print("\n🔬 Running benchmark examples\n")
    examples = []
    with jsonlines.open(benchmark_path) as reader:
        for ex in reader:
            examples.append(ex)

    results = []
    for i, example in enumerate(examples):

        question = example["inputs"]["question"]
        conversation = example["inputs"].get("conversation", "")
        expected_keywords = example.get("metadata", {}).get("expected_keywords", [])
        golden_reference = example.get("outputs", {}).get("answer", "")

        t1 = time.time()
        accuracy, coherence, retrieval = await asyncio.gather(
            judge_accuracy(question, response, golden_reference),
            judge_coherence(conversation, question, response),
            judge_coherence(conversation, question, response),
            #judge_retrieval_quality(response, context_str),
        )

        print(f"[{i+1}] Technician: {question}")
        print(f"     ✅ Accuracy: {accuracy:.2f} | 🧠 Coherence: {coherence:.2f} | 📚 Retrieval: {retrieval:.2f} | ⏱️ {t1 - t0:.2f}s\n")
        results.append((accuracy, coherence, retrieval))

    if results:
        avg = lambda idx: sum(r[idx] for r in results) / len(results)
        print(f"🏁 Benchmark complete.")
        print(f"   ✅ Avg Accuracy: {avg(0):.2f}\n   🧠 Avg Coherence: {avg(1):.2f}\n   📚 Avg Retrieval: {avg(2):.2f}\n")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", choices=["benchmark", "chat"], required=True)
    parser.add_argument("--verbose", action="store_true", help="Show full reasoning output")
    args = parser.parse_args()

    if vector_store_exists():
        from langchain_ollama import OllamaEmbeddings
        from constants import CHROMA_DB_DIR, COLLECTION_NAME, EMBED_MODEL
        docs = chunk_txt_to_docs(TEXT_FILE, strategy="semantic")
        vectordb = Chroma(persist_directory=CHROMA_DB_DIR, collection_name=COLLECTION_NAME, embedding_function=OllamaEmbeddings(model=EMBED_MODEL))
    else:
        docs, vectordb = create_vector_store()

    retriever = get_retriever("hybrid", docs, vectordb)
    chain = build_chain(retriever)

    if args.run == "chat":
        run_chat(chain, retriever, verbose=args.verbose)
    elif args.run == "benchmark":
        asyncio.run(run_benchmark(chain, retriever))

if __name__ == "__main__":
    main()

