import os
from rich import print
from langchain.schema import Document
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings
from constants import EMBED_MODEL, CHROMA_DB_DIR, COLLECTION_NAME

def embed_documents(documents: list[Document], overwrite: bool = False) -> Chroma:
    if os.path.exists(CHROMA_DB_DIR) and not overwrite:
        print("[yellow]⚠️ Skipping embedding - DB already exists[/yellow]")
        return Chroma(persist_directory=CHROMA_DB_DIR, collection_name=COLLECTION_NAME, embedding_function=OllamaEmbeddings(model=EMBED_MODEL))

    print("[green]🔁 Embedding and saving documents...[/green]")
    vectordb = Chroma.from_documents(
        documents=documents,
        collection_name=COLLECTION_NAME,
        embedding=OllamaEmbeddings(model=EMBED_MODEL),
        persist_directory=CHROMA_DB_DIR,
    )
    vectordb.persist()
    print("[green]✅ Vectorstore created and persisted[/green]")
    return vectordb
