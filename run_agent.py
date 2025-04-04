import os
import logging
import time
from PyPDF2 import PdfReader
from rich import print
from langchain_core.runnables import RunnableLambda
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_experimental.text_splitter import SemanticChunker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("rag_chat.log"), logging.StreamHandler()],
)

OLLAMA_MODEL = "mistral"
EMBED_MODEL = "nomic-embed-text"
COLLECTION_NAME = "semantic-chunks"
CONTENT_FILE = "data/content.pdf"

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


def build_rag_chain(documents):
    print("[yellow]📦 Creating vector store and retriever...[/yellow]")
    logging.info("Building Chroma vectorstore with semantic chunks")

    vectorstore = Chroma.from_documents(
        documents=documents,
        collection_name=COLLECTION_NAME,
        embedding=OllamaEmbeddings(model=EMBED_MODEL),
    )
    retriever = vectorstore.as_retriever()

    prompt_template = ChatPromptTemplate.from_template(
        # Control verbosity through the prompt instead of modifying ChatOllama
        # globally, to avoid limiting output length across all completions.
        """ You are an AI assistant helping a technician troubleshoot
        appliances. Use the context and conversation history to
        answer the technician's question.
        Your response must be a single sentence, clear and specific.
        Your response must be no more than 30 tokens.

        Context:
        {context}

        Conversation history:
        {conversation}

        Technician: {question}
        AI Assistant:"""
    )

    return (
        {
            "context": RunnableLambda(
                lambda x: retriever.invoke(x["question"])
            ),
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

    print(f"[yellow]📖 Reading PDF content from {CONTENT_FILE}...[/yellow]")
    logging.info("Loading and parsing PDF")

    pdfdoc = PdfReader(CONTENT_FILE)
    raw_text = "".join([page.extract_text() or "" for page in pdfdoc.pages])

    print("[yellow]🧠 Performing semantic chunking...[/yellow]")
    logging.info("Chunking document using SemanticChunker")

    text_splitter = SemanticChunker(OllamaEmbeddings(model=EMBED_MODEL))
    documents = text_splitter.create_documents([raw_text])

    print(f"[green]✅ Loaded and chunked {len(documents)} documents[/green]")
    return documents


def main():
    print("[bold green]💬 Agentic RAG Chat Interface[/bold green]")
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
