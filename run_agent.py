import os
import argparse
from rich import print
from langchain_community.docstore.document import Document
from langchain_community.chat_models import ChatOllama
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_core.runnables.passthrough import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_experimental.text_splitter import SemanticChunker

# Constants
OLLAMA_MODEL = "mistral"
EMBED_MODEL = "nomic-embed-text"
COLLECTION_NAME = "semantic-chunks"
CONTENT_PATH = "data/content.txt"

# === Initialise LLM === #
local_llama = ChatOllama(model=OLLAMA_MODEL)


class ConversationMemory:
# === Simple Memory Demo === #
    def __init__(self):
        self.history = []
    
    def add_turn(self, role, message):
        self.history.append(f"{role}: {message}")

    def get_history(self):
        return "\n".join(self.history)

    def format_history(self):
        return "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in self.history])


def build_rag_chain(documents):
# === RAG Chain === #
    vectorstore = Chroma.from_documents(
        documents=documents,
        collection_name="semantic-chunks",
        embedding=OllamaEmbeddings(model=EMBED_MODEL),
    )

    retriever = vectorstore.as_retriever()

    prompt_template = ChatPromptTemplate.from_template("""
    You are an AI assistant helping a tehcnician troubleshoot appliances.
    Use the following context and conversation history to answer the current question.

    Context:
    {context}

    Conversation history:
    {conversation}

    Technician: {question}
    AI Assistant:
    """
    )

    chain = (
        {"context": retriever, 
         "conversation": lambda x: x["conversation"],
         "question": lambda x: x["question"],
        }
        | prompt_template
        | local_llama
        | StrOutputParser()
    )

    return chain



def load_and_chunk_documents():
    from langchain_experimental.text_splitter import SemanticChunker
    with open("data/content.txt", "r", encoding="utf-8") as file:
        text = file.read()
    text_splitter = SemanticChunker(OllamaEmbeddings(model="nomic-embed-text"))
    return text_splitter.create_documents([text])



def main():
    parser = argparse.ArgumentParser(description="Semantic Search CLI using LangChain")
    parser.add_argument(
        "--query", type=str, required=True, help="Technician's question"
    )
    
    args = parser.parse_args()
    memory = ConversationMemory()
    query = args.query

    documents = load_and_chunk_documents()
    chain = build_rag_chain(documents)

    memory.add_turn("Technician", query)

    conversation_input = {
        "question": query,
        "conversation": memory.get_history(),
    }
    response = chain.invoke(conversation_input)
    print(response)
    memory.add_turn(user_question, response)


if __name__ == "__main__":
    main()
