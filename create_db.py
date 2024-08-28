import json
from retrieve import chromadb_client, sentence_transformer_ef
from utils import format_document
from config import DATA_PATH, DATA_LIMIT_DB, COLLECTION_NAME

def parse_convfinqa_dataset(filepath, limit: int = None):
    with open(filepath, 'r') as f:
        data = json.load(f)
    docs = []
    
    if limit:
        data = data[:limit]

    for entry in data:
        doc = format_document(entry)
        docs.append(doc)
    
    return docs


try:
    chromadb_client.delete_collection(name=COLLECTION_NAME)
    chromadb_client.clear_system_cache()
except ValueError:
    pass

db = chromadb_client.create_collection(name=COLLECTION_NAME, embedding_function=sentence_transformer_ef)

docs = parse_convfinqa_dataset(DATA_PATH, limit=DATA_LIMIT_DB)
ids = [doc.id for doc in docs]
texts = [doc.page_content for doc in docs]
metadatas = [doc.metadata for doc in docs]

db.add(ids=ids, documents=texts, metadatas=metadatas)


