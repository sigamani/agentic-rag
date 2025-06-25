"""
Mock retrieval system for testing the financial RAG pipeline without requiring vector databases.
"""
from langchain_core.documents import Document
from typing import List

class MockRelevantDocumentRetriever:
    """Mock document retriever that returns realistic financial documents."""
    
    def __init__(self, data_path: str = None):
        self.data_path = data_path
        self.mock_documents = [
            Document(
                page_content="In 2008, the net cash from operating activities was $200,000. This represented a strong performance in the company's core operations.",
                metadata={"id": "financial-doc-2008", "year": "2008"}
            ),
            Document(
                page_content="In 2009, the net cash from operating activities increased to $258,620. This shows continued improvement in cash generation.",
                metadata={"id": "financial-doc-2009", "year": "2009"}
            ),
            Document(
                page_content="The company's cash flow statement shows consistent growth in operating activities over the two-year period from 2008 to 2009.",
                metadata={"id": "financial-analysis-2008-2009", "type": "analysis"}
            ),
            Document(
                page_content="Revenue for 2008 was $1.2 million, while 2009 revenue reached $1.5 million, indicating strong business growth.",
                metadata={"id": "revenue-comparison", "type": "revenue"}
            ),
            Document(
                page_content="The working capital ratio improved from 1.4 in 2008 to 1.7 in 2009, showing better liquidity management.",
                metadata={"id": "working-capital-analysis", "type": "ratios"}
            )
        ]
    
    def query(self, question: str, top_k: int = 5) -> List[Document]:
        """Mock query that returns relevant documents based on keywords."""
        question_lower = question.lower()
        
        # Filter documents based on question content
        relevant_docs = []
        
        if "cash" in question_lower and "operating" in question_lower:
            # Return cash flow related documents
            relevant_docs = [doc for doc in self.mock_documents if "cash" in doc.page_content.lower()]
        elif "revenue" in question_lower:
            # Return revenue related documents  
            relevant_docs = [doc for doc in self.mock_documents if "revenue" in doc.page_content.lower()]
        elif "ratio" in question_lower or "working capital" in question_lower:
            # Return ratio analysis documents
            relevant_docs = [doc for doc in self.mock_documents if "ratio" in doc.page_content.lower()]
        else:
            # Return general financial documents
            relevant_docs = self.mock_documents[:top_k]
        
        return relevant_docs[:top_k]
    
    def dense_query(self, question: str, top_k: int = 5) -> List[Document]:
        """Mock dense retrieval - same as regular query for testing."""
        return self.query(question, top_k)

class MockVectorStore:
    """Mock vector store for similarity search."""
    
    def __init__(self):
        self.retriever = MockRelevantDocumentRetriever()
    
    def similarity_search(self, query: str, k: int = 5) -> List[Document]:
        """Mock similarity search."""
        return self.retriever.query(query, k)

# Create mock instances
vector_store = MockVectorStore()

def load_chroma_vector_store(persist_dir: str = "mock_chroma", embedding_model: str = "mock-embedding"):
    """Mock vector store loader."""
    return vector_store