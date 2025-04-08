import re
from abc import ABC, abstractmethod
from typing import List
from langchain.schema import Document
from langchain_experimental.text_splitter import SemanticChunker as LangchainSemanticChunker
from langchain_ollama import OllamaEmbeddings




# === Base Chunker ===
class BaseChunker(ABC):
    """
    Abstract base class for all chunkers.
    Ensures a uniform interface: chunk() and create_documents().
    """

    def __init__(self, metadata: dict = None):
        self.metadata = metadata or {}

    def create_documents(self, text: str) -> List[Document]:
        docs = self.chunk(text)
        for d in docs:
            d.metadata.update(self.metadata)
        return docs

    @abstractmethod
    def chunk(self, text: str) -> List[Document]:
        pass



class SemanticChunker:
    def __init__(self, model_name="all-minilm"):
        self.splitter = LangchainSemanticChunker(OllamaEmbeddings(model=model_name))

    def create_documents(self, text: str) -> list[Document]:
        # Converts raw string to LangChain Document, then splits
        input_doc = Document(page_content=text)
        return self.splitter.split_documents([input_doc])


# === Agentic Chunker (Stub) ===
class AgenticChunker(BaseChunker):
    def chunk(self, text: str) -> List[Document]:
        chunks = text.split("\n\n")  # placeholder logic
        return [Document(page_content=chunk.strip()) for chunk in chunks if chunk.strip()]


# === Title Chunker ===
class TitleChunker(BaseChunker):
    def chunk(self, text: str) -> List[Document]:
        sections = re.split(r"(?m)^([A-Z\s]{5,})$", text)
        docs = []
        for i in range(1, len(sections), 2):
            title = sections[i].strip()
            body = sections[i + 1].strip() if i + 1 < len(sections) else ""
            if body:
                docs.append(Document(page_content=body, metadata={"title": title}))
        return docs

def get_chunker(strategy: str):
    strategy = strategy.lower()
    if strategy == "semantic":
        return SemanticChunker()
    elif strategy == "agentic":
        return AgenticChunker()
    elif strategy == "title":
        return TitleChunker()
    else:
        raise ValueError(f"Unsupported chunking strategy: {strategy}")
