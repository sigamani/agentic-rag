import re
from typing import List
from langchain.schema import Document
from langchain_experimental.text_splitter import SemanticChunker as LangchainSemanticChunker
from langchain_ollama import OllamaEmbeddings

# Base class
class BaseChunker:
    def __init__(self, metadata: dict = None):
        self.metadata = metadata or {}

    def create_documents(self, text: str) -> List[Document]:
        docs = self.chunk(text)
        for d in docs:
            d.metadata.update(self.metadata)
        return docs

    def chunk(self, text: str) -> List[Document]:
        raise NotImplementedError


# Semantic chunking using embeddings
class SemanticChunker(BaseChunker):
    def __init__(self, model_name="all-minilm"):
        super().__init__()
        self.splitter = LangchainSemanticChunker(OllamaEmbeddings(model=model_name))

    def chunk(self, text: str) -> List[Document]:
        input_doc = Document(page_content=text)
        return self.splitter.split_documents([input_doc])


# Placeholder agentic chunker
class AgenticChunker(BaseChunker):
    def chunk(self, text: str) -> List[Document]:
        chunks = text.split("\n\n")
        return [Document(page_content=chunk) for chunk in chunks if chunk]


# Title-based chunker
class TitleChunker(BaseChunker):
    def chunk(self, text: str) -> List[Document]:
        sections = re.split(r"(?m)^([A-Z\\s]{5,})$", text)
        docs = []
        for i in range(1, len(sections), 2):
            title = sections[i]
            body = sections[i + 1] if i + 1 < len(sections) else ""
            if body:
                docs.append(Document(page_content=body, metadata={"title": title}))
        return docs


# Optional chunker selector
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
