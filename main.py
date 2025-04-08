import argparse
import json
import time
import logging
from rich import print

from constants import BENCHMARK_FILE, CHAT_MODEL, TEXT_FILE
from create_vector_store import create_vector_store, vector_store_exists
from parser import chunk_txt_to_docs

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

        Here is the short answer...
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


def run_chat(chain, verbose=False):
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

        print("[yellow]🧠 Thinking...[/yellow]")
        start = time.time()
        response = chain.invoke({"question": query, "conversation": conversation})
        end = time.time()

        if verbose:
            print(f"[bold magenta]AI Assistant:[/bold magenta] {response}")
        else:
            final = response.split("### Final Response")[-1].strip()
            trimmed = " ".join(final.split()[:30])
            print(f"[bold magenta]AI Assistant:[/bold magenta] {trimmed} ...")

        print(f"[dim]⏱️ Response time: {end - start:.2f}s[/dim]\n")
        history.append(f"AI Assistant: {response}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", choices=["benchmark", "chat"], required=True)
    parser.add_argument("--verbose", action="store_true", help="Show full reasoning output")
    args = parser.parse_args()

    if vector_store_exists():
        from langchain_community.vectorstores import Chroma
        from langchain_ollama import OllamaEmbeddings
        from constants import CHROMA_DB_DIR, COLLECTION_NAME, EMBED_MODEL
        from retrieval import get_retriever

        docs = chunk_txt_to_docs(TEXT_FILE, strategy="semantic")
        vectordb = Chroma(persist_directory=CHROMA_DB_DIR, collection_name=COLLECTION_NAME, embedding_function=OllamaEmbeddings(model=EMBED_MODEL))
    else:
        docs, vectordb = create_vector_store()


    retriever = get_retriever("hybrid", docs, vectordb)
    chain = build_chain(retriever)

    if args.run == "chat":
        run_chat(chain, verbose=args.verbose)


if __name__ == "__main__":
    main()
