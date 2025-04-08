import argparse
import json
import time
import logging
from rich import print

from constants import BENCHMARK_FILE, CHAT_MODEL, TEXT_FILE
from create_vector_store import create_vector_store, vector_store_exists
from retriever_setup import setup_retriever

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda

logging.basicConfig(level=logging.INFO)

def build_chain(retriever):
    prompt = ChatPromptTemplate.from_template(
        """
        ### Assistant Thinking Log
        First, write down what you believe the technician is trying to solve based on the {conversation}.
        Then list 2–3 things you are confident about from the {context}.
        Then list 1–2 things you are uncertain about and need clarification on.
        Only then begin your final assistant reply.

        ---

        ### Final Response (in the usual format)
        """
    )
    llm = ChatOllama(model=CHAT_MODEL, temperature=0.2, max_tokens=500)
    return (
        {
            "context": RunnableLambda(lambda x: retriever.get_relevant_documents(x["question"])),
            "conversation": lambda x: x["conversation"],
            "question": lambda x: x["question"],
        }
        | prompt
        | llm
        | StrOutputParser()
    )

def run_benchmark(chain):
    with open(BENCHMARK_FILE, "r") as f:
        examples = json.load(f)

    for ex in examples[:1]:
        print("\n[yellow]Technician:[/yellow]", ex["question"])
        print("[blue]History:[/blue]", ex.get("conversation", ""))
        start = time.time()
        response = chain.invoke({"question": ex["question"], "conversation": ex.get("conversation", "")})
        print("[magenta]Assistant:[/magenta]", response)
        print(f"[dim]⏱️ Took {time.time() - start:.2f}s[/dim]")

def run_chat(chain):
    print("[bold green]💬 RAG Chat Interface[/bold green]")
    print("[dim]Type 'exit' to quit.[/dim]\n")
    history = []
    while True:
        query = input("[bold cyan]Technician:[/bold cyan] ").strip()
        if query.lower() in ["exit", "quit"]:
            print("[italic]👋 Goodbye![/italic]")
            break
        history.append(f"Technician: {query}")
        conversation = "\n".join(history)
        start = time.time()
        response = chain.invoke({"question": query, "conversation": conversation})
        print(f"[bold magenta]AI Assistant:[/bold magenta] {response}")
        print(f"[dim]⏱️ Response time: {time.time() - start:.2f}s[/dim]\n")
        history.append(f"AI Assistant: {response}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", choices=["benchmark", "chat"], required=True)
    args = parser.parse_args()

    docs, vectordb = create_vector_store()

    if vector_store_exists():
        print("[blue]💾 Using existing vectorstore from disk[/blue]")
        from langchain_community.vectorstores import Chroma
        from langchain_ollama import OllamaEmbeddings
        from constants import CHROMA_DB_DIR, COLLECTION_NAME, EMBED_MODEL
        from parser import chunk_txt_to_docs
        docs = chunk_txt_to_docs(TEXT_FILE, strategy="semantic")

        vectordb = Chroma(persist_directory=CHROMA_DB_DIR, collection_name=COLLECTION_NAME, embedding_function=OllamaEmbeddings(model=EMBED_MODEL))
    else:
        print("[red]⚠️ No valid vectorstore found. Rebuilding...[/red]")
        docs, vectordb = create_vector_store()

    retriever = setup_retriever("hybrid", docs, vectordb)
    chain = build_chain(retriever)

    if args.run == "benchmark":
        run_benchmark(chain)
    elif args.run == "chat":
        run_chat(chain)

if __name__ == "__main__":
    main()
