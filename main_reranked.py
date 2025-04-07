
from langchain_community.vectorstores import Chroma
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain.schema.runnable import RunnableMap
from langchain.prompts import PromptTemplate
from langchain.docstore.document import Document

from utils.title_chunker import TitleChunker
import tiktoken
import re

# ========== CONFIG ==========
DATA_FILE = "data/content.txt"
EMBEDDING_MODEL = "all-minilm"
LLM_MODEL = "mistral"
MAX_CHUNK_TOKENS = 256
TOP_K = 8
TOP_K_RERANK = 3
# ============================

def count_tokens(text, model_name="gpt2"):
    enc = tiktoken.get_encoding(model_name)
    return len(enc.encode(text))

def safe_trim(text, max_tokens, encoding_name="gpt2"):
    enc = tiktoken.get_encoding(encoding_name)
    token_ids = enc.encode(text)
    if len(token_ids) <= max_tokens:
        return text
    trimmed_text = enc.decode(token_ids[:max_tokens])
    # Only include complete sentences
    sentences = re.findall(r'.*?[.!?]', trimmed_text, re.DOTALL)
    result = ""
    for sentence in sentences:
        if count_tokens(result + sentence, encoding_name) <= max_tokens:
            result += sentence + " "
        else:
            break
    return result.strip()

def load_documents():
    with open(DATA_FILE, "r") as f:
        raw_text = f.read()
    chunker = TitleChunker()
    chunks = chunker.chunk(raw_text)
    trimmed = []
    for chunk in chunks:
        trimmed_text = safe_trim(chunk['text'], MAX_CHUNK_TOKENS)
        metadata = {
            "title": chunk.get("title", "Untitled"),
            "page": chunk.get("page", -1)
        }
        trimmed.append(Document(page_content=trimmed_text, metadata=metadata))
    return trimmed

def rerank(query, docs, embedding_model, top_k=TOP_K_RERANK):
    query_vec = embedding_model.embed_query(query)
    doc_scores = []
    for doc in docs:
        doc_vec = embedding_model.embed_documents([doc.page_content])[0]
        score = sum(a*b for a, b in zip(query_vec, doc_vec))
        doc_scores.append((score, doc))
    reranked = sorted(doc_scores, key=lambda x: x[0], reverse=True)
    return [doc for _, doc in reranked[:top_k]]

def format_answer(answer, source_docs):
    references = []
    for doc in source_docs:
        page = doc.metadata.get("page", "?")
        title = doc.metadata.get("title", "Unknown Section")
        references.append(f"See Page {page}: '{title}'")
    reference_text = "\n".join(references)
    return f"{answer}\n\n{reference_text}"

def run_assistant(query):
    docs = load_documents()
    embedding_model = OllamaEmbeddings(model=EMBEDDING_MODEL)
    vectordb = Chroma.from_documents(docs, embedding_model)
    retriever = vectordb.as_retriever(search_kwargs={"k": TOP_K})
    retrieved_docs = retriever.invoke(query)
    final_docs = rerank(query, retrieved_docs, embedding_model)

    llm = ChatOllama(model=LLM_MODEL, temperature=0.2, max_tokens=30)
    prompt = PromptTemplate.from_template(
        "You are a concise technical assistant. Respond in max 30 tokens.\n\nQuestion: {question}\n\nAnswer:"
    )

    chain = (
        RunnableMap({
            "question": lambda x: x,
            "context": lambda _: final_docs
        })
        | (lambda inputs: {
            "result": llm.invoke(prompt.format(question=inputs["question"])).content,
            "source_documents": final_docs
        })
        | (lambda outputs: format_answer(outputs["result"], outputs["source_documents"]))
    )
    return chain.invoke(query)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", type=str, required=True)
    args = parser.parse_args()
    print(run_assistant(args.query))
