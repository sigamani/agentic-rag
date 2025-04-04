# 🧠 Agentic RAG Strategy Document

This document outlines the technical strategy for building a **Retrieval-Augmented Generation (RAG)** assistant optimised for technician troubleshooting queries using dishwasher repair manuals.

---

## 📌 Solution Overview

We are building an **Agentic RAG chatbot** that combines:

- **Agent-aware semantic chunking** for high retrieval precision
- **Hybrid retrieval** using both dense vector similarity and structured metadata filters
- **Streaming local LLM inference** (via Ollama running Mistral or DeepSeek)
- **Conversational memory** to handle multi-turn queries with full coherence
- ✅ Optional backend: FastAPI for deployment or Streamlit for demos

---

## 🧱 Architecture Components

| Component     | Strategy                                                                 |
|---------------|--------------------------------------------------------------------------|
| Chunking      | `SemanticChunker` with agent-aware tuning for error codes, components, procedures |
| Vector DB     | `ChromaDB` for fast prototyping. Switch to Pinecone for long-term enterprise use, with metadata filtering (`error_code`, `model_id`, `component`) |
| Embeddings    | `OllamaEmbeddings` using `nomic-embed-text`, configurable for model experiments |
| LLM           | Local `ChatOllama` inference with `mistral`, streamed to CLI |
| Retrieval     | Hybrid retriever: `MultiQueryRetriever + SelfQueryRetriever` (LangChain) |
| Memory        | Custom ConversationMemory object or `ConversationBufferMemory` |
| RAG Chain     | Custom `ConversationalRetrievalChain` using LangChain primitives |

---

## 🎯 Recommended Benchmarks

| Metric                | Target                          | Rationale                                                |
|-----------------------|----------------------------------|----------------------------------------------------------|
| Latency (p95)         | ≤ 3s total                      | Smooth CLI or Streamlit UX                              |
| Latency (mean)        | ≤ 1.5–2s                        | Avoid sluggish response                                 |
| Retrieval Accuracy    | ≥ 90% chunk relevance           | Relevant docs per query                                 |
| Response Quality      | ≥ 4/5                           | Human eval or LLM grader                                |
| Contextual Coherence  | 100% (short multi-turn)         | Intent preserved across 2–5 turns                       |

---

## ⚡ Performance Enhancements

| Feature                   | Benefit                                                           |
|---------------------------|-------------------------------------------------------------------|
| SemanticChunker           | Groups semantically coherent text for better retrieval            |
| Metadata Filtering        | Targets relevant error codes or models (e.g. E4)                  |
| Local LLM + Streaming     | Low-latency, fast interactive experience                          |
| Agentic Chunk Annotation  | Aligns chunks with technician phrasing (e.g., “doesn’t drain”)    |
| LangSmith Integration     | Token tracing, retrieval inspection, judge-based evaluation       |
| W&B Integration           | Tracks latency, memory, throughput, errors, and hardware benchmarks |

---

## 🧠 Chunking Strategy

```python
from langchain.text_splitter import SemanticChunker
from langchain_community.embeddings import OllamaEmbeddings

text = load_pdf_to_text("dishwasher.pdf")

# Semantic chunking
embeddings = OllamaEmbeddings(model="nomic-embed-text")
splitter = SemanticChunker(embeddings)
chunks = splitter.split_text(text)
```

### Metadata Heuristics (To Add)

- `error_code`: e.g. `E4`
- `component`: Drain Pump, Hose
- `step_type`: “Check”, “Run”, “Inspect”
- `model_id`: e.g. `Model 18 ADA`

---

## 🚀 Backend API (FastAPI)

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Query(BaseModel):
    question: str
    history: list[str]

@app.post("/ask")
def ask(query: Query):
    response = qa.run(query.question)
    return {"answer": response}
```

---

## 🔁 Retrieval Optimisation (Hybrid)

```python
from langchain.retrievers import MultiQueryRetriever
from langchain.retrievers.self_query.base import SelfQueryRetriever

retriever = MultiQueryRetriever.from_llm(
    llm=ChatOllama(...),
    retriever=vectorstore.as_retriever()
)
# OR
retriever = SelfQueryRetriever.from_llm(
    llm,
    vectorstore,
    document_content_description="manual pages"
)
```

---

## 🔄 Conversational Memory

```python
from langchain.memory import ConversationBufferMemory
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

from langchain.chains import ConversationalRetrievalChain
qa = ConversationalRetrievalChain.from_llm(
    llm=ChatOllama(model="mistral:instruct"),
    retriever=hybrid_retriever,
    memory=memory,
    return_source_documents=True
)
```

---

## 🧪 Benchmarking + Observability

- **Weights & Biases**: Track latency, throughput, resource usage, chunk count, error rates.
- **LangSmith**: Run accuracy tests using LLM judge to compare RAG outputs vs expected completions.
- **benchmark_config.yaml**: Central config for testing multiple documents, questions, and response quality.

---

## 📌 Summary

This agentic RAG architecture is designed for rapid prototyping and accuracy-critical environments like appliance support. By using chunk-aware logic, hybrid retrieval, local inference, and evaluation tooling, we ensure relevance, responsiveness, and reliability — even with multi-turn technician queries.
