import os
import argparse
from rich import print
from langchain_community.docstore.document import Document
from langchain_community.chat_models import ChatOllama
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.runnables.passthrough import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_experimental.text_splitter import SemanticChunker

# === Globals === #
OLLAMA_MODEL = "mistral"
EMBED_MODEL = "nomic-embed-text"
COLLECTION_NAME = "semantic-chunks"
CONTENT_FILE = "data/content.txt"

# === Initialise LLM === #
local_llama = ChatOllama(model=OLLAMA_MODEL)


# === RAG Chain === #
def build_rag_chain(documents, collection_name):
    vectorstore = Chroma.from_documents(
        documents=documents,
        collection_name=collection_name,
        embedding=OllamaEmbeddings(model=EMBED_MODEL),
    )

    retriever = vectorstore.as_retriever()

    prompt_template = """
    You are an AI assistant helping a technician diagnose issues with Whirlpool dishwashers. 
    Your goal is to provide short, clear, and actionable advice based only on the provided context and conversation history.

    Guidelines:
    - Speak in short, helpful sentences (maximum of 2). 
    - Limit your output to 80 tokens.
    - Never hallucinate features or errors.
    - If a technician has already performed a step, suggest the next most logical troubleshooting action.
    - Avoid repeating prior instructions unless asked.
    - Assume the technician is hands-on with the dishwasher.
    - Be calm, precise, and task-focused.

    Context: {context}
    Question: {question}

    AI assistant:
    """.strip()

    prompt = ChatPromptTemplate.from_template(prompt_template)

    return (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | local_llama
        | StrOutputParser()
    )


# === Semantic Chunking === #
def semantic_chunk_text(text):
    text_splitter = SemanticChunker(
        OllamaEmbeddings(model=EMBED_MODEL), breakpoint_threshold_type="percentile"
    )
    return text_splitter.create_documents([text])


# === Load Text from File === #
def load_text(filepath):
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Could not find file: {filepath}")
    with open(filepath, "r", encoding="utf-8") as file:
        return file.read()


# === Run Semantic Search === #
def run_semantic_search(user_query):
    print("[bold green]Performing semantic chunking...[/bold green]")
    text = load_text(CONTENT_FILE)
    documents = semantic_chunk_text(text)

    print("[bold green]Running RAG pipeline...[/bold green]")
    chain = build_rag_chain(documents, COLLECTION_NAME)
    result = chain.invoke(user_query)
    print("\n[bold yellow]AI Assistant:[/bold yellow]", result)


# === CLI Entrypoint === #
def main():
    parser = argparse.ArgumentParser(description="Semantic Search CLI using LangChain")
    parser.add_argument(
        "--query", type=str, required=True, help="The user query to answer"
    )
    args = parser.parse_args()

    run_semantic_search(args.query)


if __name__ == "__main__":
    main()
