from concurrent.futures import ThreadPoolExecutor, as_completed
from langchain_core.documents import Document
from langchain.vectorstores.base import VectorStore
from typing import Dict, List, Union

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
