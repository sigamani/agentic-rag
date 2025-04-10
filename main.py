import argparse
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain


def load_vectorstore(persist_dir: str):
    embedder = OllamaEmbeddings(model="nomic-embed-text")
    return Chroma(persist_directory=persist_dir, embedding_function=embedder)


def get_conversational_chain():
    vectordb = load_vectorstore("vectorstore")
    retriever = vectordb.as_retriever(search_kwargs={"filter": {"document_id": "whirlpool"}})

    memory = ConversationBufferMemory(
        memory_key="chat_history", return_messages=True, input_key="question"
    )

    prompt = PromptTemplate.from_template(
        """
        You are a helpful assistant. Use the following context to answer the user's question.
        Maintain the conversation history and build upon previous answers when necessary.

        Context:
        {context}

        Chat History:
        {chat_history}

        Question:
        {question}

        Provide a helpful, concise answer followed by a short summary of key points.
        """
    )

    chain = ConversationalRetrievalChain.from_llm(
        llm=ChatOllama(model="mistral"),
        retriever=retriever,
        memory=memory,
        combine_docs_chain_kwargs={"prompt": prompt},
        return_source_documents=True
    )
    return chain


def main():
    parser = argparse.ArgumentParser(description="Conversational RAG over Whirlpool vectorstore")
    parser.add_argument("--query", type=str, required=True, help="Your user question")
    args = parser.parse_args()

    chain = get_conversational_chain()
    result = chain.invoke({"question": args.query})

    print("\n=== Assistant ===")
    print(result["answer"])


if __name__ == "__main__":
    main()
