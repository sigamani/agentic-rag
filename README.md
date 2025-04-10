
# 🧠 Whirlpool RAG Assistant (Multimodal-Aware)

This repo implements a document-grounded conversational RAG assistant for Whirlpool dishwasher troubleshooting, built with LangChain, Chroma, and Ollama (Mistral). It optionally parses and grounds from structured PDFs with diagrams and tables using Gemini 1.5 Flash.

---

## ✅ What This Assistant Does

- Loads a persistent vectorstore of embedded Whirlpool manual chunks
- Supports both **CLI chat** and **single-query** modes
- Uses `document_id` filtering for scoped retrieval (Whirlpool-only)
- Stores and filters on `section_title` for source grounding
- Generates responses using **Mistral (Ollama)** with optional summarisation
- Extracts structured documents using **Gemini 1.5 Flash** (text, tables, images)
- Keeps logs of all interactions, latency, and fallback decisions

---

## 🔍 Prompting & Design Rationale

Prompts are structured to:
- Enforce task alignment (dishwasher only)
- Use multi-turn chat history
- Minimise hallucinations
- Summarise with a distillation prompt (2 sentences, actionable)

Retrieval match is scored simply via token overlap and fallback responses are triggered if low match is detected.

---

## 💡 Known Limitations

- ❌ No multimodal retriever interface (images extracted but unused at runtime)
- ❌ Retrieval match scoring is naive (non-semantic)
- ❌ Summarisation not cached (redundant compute)
- ❌ Chroma has scaling limits — Pinecone planned for production
- ❌ No use of section filtering yet, despite indexing
- ❌ No prompt injection protection

---

## 🔧 Future Enhancements

- 🖼️ **Multimodal interface**: use retrieved diagrams and annotated screenshots
- 🌲 **Pinecone migration**: scalable, production-ready vector infra
- 🤖 **LangGraph agent orchestration**: stateful flows, LangSmith logging
- 🧪 **RAG benchmark integration**: judge LLM scoring, hybrid ablations
- 📚 **Section-aware responses**: “See Section X (Page Y)...” style

---

## 🧰 Core Stack

| Component     | Role                                              |
|---------------|---------------------------------------------------|
| LangChain     | Chain management, memory, retrieval abstractions  |
| Ollama + Mistral | Fast local generation and summarisation       |
| ChromaDB      | Local persistent vector store                     |
| Gemini Flash  | PDF → structured text & table extraction          |
| LangGraph     | Used for document-agent workflows                 |
| HybridRetriever | Optional BM25 + dense fusion for better recall |

---

## ✅ Why This Works

This agent handles technical queries like "E4.1 error" and "filter not draining" with grounded, document-scoped responses. It integrates prompt safety, source metadata, and hybrid-ready architecture — ideal for scaling into an enterprise-grade troubleshooting assistant.




---

## 🚀 How to Run This Repo

### Install dependencies
```bash
pip install -r requirements.txt
```

Make sure [Ollama](https://ollama.com/) is installed and running with the Mistral model:

```bash
ollama run mistral
```

Optional: Gemini-based extraction requires access to the Gemini 1.5 Flash API via `google.generativeai`.

---

### Start the Chat Assistant
Run the interactive assistant:

```bash
python main.py --chat
```

Or ask a single question directly:

```bash
python main.py --query "What does the E4.1 code mean?"
```

Logs and outputs will be saved to `main.log`.

---

---

## 🧪 Testing & CI Status

- 🚫 This repo **does not currently include unit tests**
- ⚠️ The CI/CD pipeline is **not functioning** — no automated build, test, or deployment setup is active
- ✅ These components are planned in the future as the codebase stabilizes and interface contracts are formalized

---

## 📊 Retrieval & Benchmarking Notes

The current live assistant uses:
```python
retriever = vectordb.as_retriever(search_kwargs={"filter": {"document_id": "whirlpool"}})
```
This is a **pure dense retriever** using semantic search over Chroma — not the hybrid version.

However, hybrid retrieval was tested and benchmarked using LangSmith, and the results are available here:  
🔗 [Benchmark results (LangSmith logs)](https://github.com/sigamani/agentic-rag/tree/main/logs/hybrid/semantic/mistral_all-minilm/structured_reasoning_v1)

---

## 🔍 Chunking Methods Tested

During experimentation, multiple chunking techniques were evaluated:

- `AgenticChunker`: uses role-structured or layout-aware segmentation
- `AgenticGraphChunker`: combines document structure + section links
- `SemanticChunker`: based on cosine similarity and embedding cohesion

Despite the advanced graph and multimodal-aware chunkers, **semantic chunking with cosine similarity** performed **just as well** in terms of retrieval precision and generation quality when paired with extracted multimodal descriptions.

These findings shaped the current design toward simplicity, performance, and reproducibility.
