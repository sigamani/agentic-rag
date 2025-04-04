import os
import argparse
from PyPDF2 import PdfReader
from rich import print
from langchain_core.runnables import RunnableLambda
from langchain_community.docstore.document import Document
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_ollama import ChatOllama
from langchain_core.runnables.passthrough import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_experimental.text_splitter import SemanticChunker

# Constants
OLLAMA_MODEL = "mistral"
EMBED_MODEL = "nomic-embed-text"
COLLECTION_NAME = "semantic-chunks"
CONTENT_FILE = "data/content.pdf"

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
        return "\n".join([f"{msg['role']}: {msg['content']}" for msg in self.history])


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
    Your answer should summarise your findings in more more than 20 tokens.

    Context:
    {context}

    Conversation history:
    {conversation}

    Technician: {question}
    AI Assistant:
    """
    )

    chain = (
        {"context": RunnableLambda(lambda x: retriever.get_relevant_documents(x["question"])), 
         "conversation": lambda x: x["conversation"],
         "question": lambda x: x["question"],
        }
        | prompt_template
        | local_llama
        | StrOutputParser()
    )

    return chain


def semantic_chunk_text(text):
    text_splitter = SemanticChunker(
        OllamaEmbeddings(model=EMBED_MODEL), breakpoint_threshold_type="percentile"
    )
    return text_splitter.create_documents([text])


def load_and_chunk_documents(filepath):
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Could not find file: {filepath}")
    pdfdoc = PdfReader(filepath)
    raw_text = ""
    for i, pages in enumerate(pdfdoc.pages):
        text = pages.extract_text()
        raw_text += text   
    
    text_splitter = SemanticChunker(OllamaEmbeddings(model="nomic-embed-text"))
    return text_splitter.create_documents([raw_text])    
    return raw_text


memory = """
Technician: I’m having trouble with a Model 18 ADA dishwasher. It’s showing an error code E4 and the customer is complaining is it not draining
AI Assistant: Error code E4 can indicate drainage issue. Let’s start by checking the drain hose for kinks or blockages. Have you inspected the hose?
Technician: Yes, I’ve checked it and there doesn’t seem to be any physical obstruction.
AI Assistant: Alright, next step is to check the drain pump. Please ensure the dishwasher is turned off and unplugged before proceeding. Can you access the drain pump?
"""

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


    conversation_input = {
        "question": query,
        "conversation": memory,
    }

    print(f"conversation input: {conversation_input}")
    response = chain.invoke(conversation_input)
    print(f"response: {response}")
    memory.add_turn("Technician", query)
    memory.add_turn("AI Assistant", response)
    #memory.format_history() 
    memory.get_history() 


if __name__ == "__main__":
    main()
