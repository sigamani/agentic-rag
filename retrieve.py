from concurrent.futures import ThreadPoolExecutor, as_completed
from langchain_core.documents import Document
from langchain.vectorstores.base import VectorStore
from typing import Dict, List, Union

import json
from collections import defaultdict
from typing import List
from utils import format_document, extract_numbers  # Assuming these are defined elsewhere

from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma

def load_chroma_vector_store(persist_dir: str = "chroma_index", embedding_model: str = "nomic-embed-text"):
    embeddings = OllamaEmbeddings(model=embedding_model)
    vectordb = Chroma(persist_directory=persist_dir, embedding_function=embeddings)
    print(f"✅ Loaded vector store from {persist_dir}")
    return vectordb

class RelevantDocumentRetriever:
    def _create_question_to_document_map(self, filepath: str, limit: int = None) -> dict[str, List[Document]]:
        q2d = defaultdict(list)
        with open(filepath, "r") as f:
            data = json.load(f)

        QA_FIELDS = ["qa", *[f"qa_{i}" for i in range(10)]]
        if limit:
            data = data[:limit]

        for entry in data:
            for qa_field in set(QA_FIELDS).intersection(entry.keys()):
                q = entry[qa_field]["question"]
                formatted_doc = format_document(entry)
                q2d[q].append(formatted_doc)

        return q2d

    def __init__(self, data_path: str, limit: int = None, retriever_name: str = "default"):
        self.retriever_name = retriever_name
        self.q2d = self._create_question_to_document_map(data_path, limit=limit)

    def __call__(self, question: str, top_k: int = 10) -> List[Document]:
        return self.query(question, top_k=top_k)

    def query(self, question: str, top_k: int = 10, rerank_with_numeric: bool = True) -> List[Document]:
        docs = self.q2d.get(question, [])[:top_k]

        if rerank_with_numeric:
            q_nums = extract_numbers(question)
            docs.sort(key=lambda d: len(q_nums & extract_numbers(d.page_content)), reverse=True)

        return docs[:top_k]


def retrieve_from_vector_db(
    state: Dict, config: Dict, vector_store: VectorStore
) -> Dict:
    queries = state.get("queries", [])
    if not queries:
        return {"documents": [], "context": "No queries provided."}

    unique_docs = {}

    def search_query(query):
        return vector_store.similarity_search(
            query, k=config.get("configurable", {}).get("retrieval_k", 5)
        )

    # Parallel search
    with ThreadPoolExecutor() as executor:
        future_to_query = {
            executor.submit(search_query, query): query for query in queries
        }

        for future in as_completed(future_to_query):
            try:
                search_results = future.result()
                for doc in search_results:
                    doc_id = doc.metadata.get("id")
                    if doc_id and doc_id not in unique_docs:
                        unique_docs[doc_id] = doc
            except Exception as e:
                print(f"❌ Error retrieving for query '{future_to_query[future]}': {e}")

    results = list(unique_docs.values())

    # Log if no results
    if not results:
        print(f"⚠️ No documents retrieved for queries: {queries}")

    context = "\n\n".join([doc.page_content for doc in results]) or "NO_CONTEXT_AVAILABLE"

    return {
        "documents": results,
        "context": context,
    }
