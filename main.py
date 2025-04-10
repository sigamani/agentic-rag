# chat_graph.py

from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field
from typing import List, Optional

from langchain.schema import Document
from embedder import embed_documents
from retrieval import get_retriever
from rag_chain import build_chain

# --- Chat State ---
class ChatState(BaseModel):
    question: str
    conversation: str = ""
    answer: Optional[str] = None

# --- LangGraph nodes ---
from langchain_core.runnables import Runnable


class RAGAnswerNode(Runnable):
    def __init__(self, retriever):
        self.chain = build_chain(retriever)

    def invoke(self, input: ChatState, config=None, **kwargs) -> ChatState:
        output = self.chain.invoke({
            "question": input.question,
            "conversation": input.conversation
        })
        return ChatState(
            question=input.question,
            conversation=input.conversation + "\n" + output,
            answer=output
        )

if __name__ == "__main__":
    chroma_dir = "data/chromadb"

#    print("📦 Loading persisted Chroma vector store...")
    vectordb = embed_documents("data2/whirlpool_chunks.jsonl", overwrite=False)  # Use existing DB without re-embedding

    print("🔍 Reconstructing hybrid retriever from vector store...")
    dense_docs = vectordb.similarity_search("*", k=1000)
    retriever = get_retriever("hybrid", dense_docs, vectordb)

    builder = StateGraph(ChatState)
    builder.add_node("rag", RAGAnswerNode(retriever))

    builder.add_edge(START, "rag")
    builder.add_edge("rag", END)
    graph = builder.compile()

    print("🤖 Whirlpool assistant ready. Type 'exit' to quit.")
    conversation = ""

    while True:
        question = input("\n🔎 Question: ")
        if question.lower() in ["exit", "quit"]:
            break
        state = ChatState(question=question, conversation=conversation)
        result = graph.invoke(state)
        print("\n🧠 Answer:", result['answer'])
        conversation = result["conversation"]

