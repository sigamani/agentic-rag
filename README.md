# Agentic RAG

This repository contains a modular Retrieval-Augmented Generation (RAG) pipeline using LangChain, Ollama embeddings, and Mistral for answering technical queries in the context of appliance troubleshooting.

## 🔧 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/agentic-rag.git
cd agentic-rag
```

### 2. Set Up Virtual Environment (Optional but Recommended)
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Make Sure You Have These Installed:
- `ollama` (for running `mistral` and `nomic-embed-text` locally)
- `tesseract` (for PDF parsing, e.g. `brew install tesseract` on macOS)

## 🚀 Running the App

You can run a semantic RAG query like this:

```bash
python run_agent.py --query "I’m having trouble with a Model 18 ADA dishwasher. It’s showing an error code E4 and the customer is complaining is it not draining"
```

You can also provide prior context to simulate a running conversation:

```bash
python run_agent.py --query "I’ve accessed the pump. There’s some debris here. I’ll clean it out and see if that fixes the issue"
```

## 📁 Folder Structure

- `run_agent.py` — main entry point for your assistant
- `data/content.txt` — the reference manual used for retrieval
- `utils/agentic_chunker.py` — utility for custom chunking (if used)

## 🧠 Model Notes

- Embedding model: `nomic-embed-text` via Ollama
- Language model: `mistral` via Ollama
- Uses LangChain's `SemanticChunker` for document splitting

---

Happy troubleshooting! 🔧🤖
