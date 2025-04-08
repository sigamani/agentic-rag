import os
import logging
import time
from collections import defaultdict
from PyPDF2 import PdfReader
from rich import print
from langchain_core.runnables import RunnableLambda
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_experimental.text_splitter import SemanticChunker
from langchain.schema import Document as LCDocument
from langchain.retrievers import BM25Retriever

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("rag_chat.log"), logging.StreamHandler()],
)

OLLAMA_MODEL = "deepseek-r1:8b"
EMBED_MODEL = "all-minilm"
COLLECTION_NAME = "semantic-chunks"
CONTENT_FILE = "data/whirlpool.txt"
TOKEN_LENGTH = 500
PERSIST_PATH = "data/chroma_db"
TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"

if not TEST_MODE:
    local_llama = ChatOllama(model=OLLAMA_MODEL, temperature=0.2, max_tokens=TOKEN_LENGTH)
else:
    from langchain_core.runnables import Runnable
    local_llama = Runnable(lambda x: "Test response from mock model.")

print("[yellow]⏳ Initialising local model...[/yellow]")
logging.info("Loading ChatOllama model")
local_llama = ChatOllama(model=OLLAMA_MODEL)
print("[green]✅ Model loaded[/green]")


class ConversationMemory:
    def __init__(self):
        self.history = []

    def add_turn(self, role, message):
        self.history.append(f"{role}: {message}")

    def get_history(self):
        return "\n".join(self.history)


class HybridRetriever:
    def __init__(self, dense_retriever, docs, k=4):
        self.dense = dense_retriever
        self.k = k
        self.bm25 = BM25Retriever.from_documents(
            [LCDocument(page_content=d.page_content, metadata=d.metadata) for d in docs]
        )

    def get_relevant_documents(self, query):
        dense_results = self.dense.invoke(query)
        sparse_results = self.bm25.invoke(query)
        # Merge and deduplicate
        combined = {doc.page_content: doc for doc in dense_results + sparse_results}
        return list(combined.values())[:self.k]


def build_rag_chain(docs):
    print("[yellow]📦 Creating hybrid vector retriever...[/yellow]")
    logging.info("Building Chroma vectorstore")

    vectorstore = Chroma.from_documents(
        documents=docs,
        collection_name=COLLECTION_NAME,
        embedding=OllamaEmbeddings(model=EMBED_MODEL),
        persist_directory=PERSIST_PATH,
    )
    #vectorstore.persist()

    dense_retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
    retriever = HybridRetriever(dense_retriever, docs, k=6)

    prompt_template = ChatPromptTemplate.from_template("""
    ### Assistant Thinking Log
    First, write down what you believe the technician is trying to solve based on the {conversation}.
    Then list 2–3 things you are confident about from the {context}.
    Then list 1–2 things you are uncertain about and need clarification on.
    Only then begin your final assistant reply.

    ---

    ### Final Response (in the usual format)
    """
    )


    return (
        {
            "context": RunnableLambda(lambda x: retriever.get_relevant_documents(x["question"])),
            "conversation": lambda x: x["conversation"],
            "question": lambda x: x["question"],
        }
        | prompt_template
        | local_llama
        | StrOutputParser()
    )


def load_and_chunk_documents():
    if not os.path.exists(CONTENT_FILE):
        raise FileNotFoundError(f"Could not find file: {CONTENT_FILE}")

    with open(CONTENT_FILE, "r", encoding="utf-8") as f:
        raw_text = f.read()

    print("[yellow]🧠 Performing semantic chunking...[/yellow]")
    logging.info("Chunking document using SemanticChunker")

    text_splitter = SemanticChunker(OllamaEmbeddings(model=EMBED_MODEL))
    documents = text_splitter.create_documents([raw_text])

    print(f"[green]✅ Loaded and chunked {len(documents)} documents[/green]")
    return documents


def main():
    print("[bold green]💬 Agentic RAG Chat Interface (Hybrid Retrieval)[/bold green]")
    print("[dim]Type 'exit' to quit.[/dim]\n")

    memory = ConversationMemory()
    documents = load_and_chunk_documents()
    chain = build_rag_chain(documents)

    while True:
        query = input("[bold cyan]Technician:[/bold cyan] ").strip()
        if query.lower() in ["exit", "quit"]:
            print("[italic]👋 Goodbye![/italic]")
            break

        memory.add_turn("Technician", query)
        conversation_input = {
            "question": query,
            "conversation": memory.get_history(),
        }

        print("[yellow]🧠 Thinking...[/yellow]")
        start = time.time()
        try:
            response = chain.invoke(conversation_input)
        except Exception as e:
            logging.error("Inference error: %s", str(e))
            print(f"[red]❌ Error: {e}[/red]")
            continue
        end = time.time()

        print(f"[bold magenta]AI Assistant:[/bold magenta] {response}\n")
        print(f"[dim]⏱️ Response time: {end - start:.2f}s[/dim]")

        memory.add_turn("AI Assistant", response)


if __name__ == "__main__":
    main()
