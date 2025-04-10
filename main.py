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
        memory_key="chat_history",
        return_messages=True,
        input_key="question",
        output_key="answer",
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
    return ConversationalRetrievalChain.from_llm(
        llm=ChatOllama(model="mistral"),
        retriever=retriever,
        memory=memory,
        combine_docs_chain_kwargs={"prompt": prompt},
        return_source_documents=True,
    )

def distill_answer(full_answer: str) -> str:
    summariser_prompt = PromptTemplate.from_template(
        """
        You're a technician speaking to a colleague. Rewrite the assistant's verbose response as if you're replying in a live chat.

        Say just two short, natural sentences:
        - First: what's likely wrong, using plain English.
        - Second: what to check or try first — just **one** concrete action.

        Do not number anything.
        Do not list multiple steps or checks.
        Do not use the words \"also\", \"and then\", or \"alternatively\".
        Do not summarize everything. Focus on just one issue and one step.

        Example:
        \"Sounds like the drain pump’s jammed. Let’s check the hose for a clog first.\"

        Assistant's full response:
        {response}
        """
    )
    chain = summariser_prompt | ChatOllama(model="mistral") | StrOutputParser()
    return chain.invoke({"response": full_answer})

def main():
    parser = argparse.ArgumentParser(description="Conversational RAG over Whirlpool vectorstore")
    parser.add_argument("--query", type=str, required=True, help="Your user question")
    parser.add_argument("--verbose", action="store_true", help="Show full assistant output")
    args = parser.parse_args()

    chain = get_conversational_chain()
    result = chain.invoke({"question": args.query})

    print("\n=== Assistant ===")
    if args.verbose:
        print(result["answer"])
    else:
        print(distill_answer(result["answer"]))

if __name__ == "__main__":
    main()

