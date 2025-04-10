import argparse
import logging
import time
from functools import lru_cache
from pathlib import Path
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain

# --- Logging Setup ---
log_file = "main.log"
logging.basicConfig(
    filename=log_file,
    filemode="a",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)
logger.info("Starting Whirlpool Assistant RAG script")

@lru_cache(maxsize=1)
def load_vectorstore(persist_dir: str):
    embedder = OllamaEmbeddings(model="nomic-embed-text")
    logger.info("Loading vectorstore from: %s", persist_dir)
    return Chroma(persist_directory=persist_dir, embedding_function=embedder, collection_metadata={"cache": True})

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
        You are a helpful assistant for diagnosing and fixing dishwashers.
        Only answer if the user's question is clearly related to dishwashers.
        If it's not, politely say you're only trained to help with those.

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
    logger.info("Conversational retrieval chain created.")
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
        "Sounds like the drain pump’s jammed. Let’s check the hose for a clog first."

        Assistant's full response:
        {response}
        """
    )
    chain = summariser_prompt | ChatOllama(model="mistral") | StrOutputParser()
    return chain.invoke({"response": full_answer})

def main():
    parser = argparse.ArgumentParser(description="Conversational RAG over Whirlpool vectorstore")
    parser.add_argument("--query", type=str, help="Single user question")
    parser.add_argument("--chat", action="store_true", help="Start interactive conversation loop")
    parser.add_argument("--verbose", action="store_true", help="Show full assistant output")
    args = parser.parse_args()

    chain = get_conversational_chain()

    def respond(question):
        logger.info("User question: %s", question)
        start = time.time()
        result = chain.invoke({"question": question})
        elapsed = time.time() - start
        logger.info("Chain response time: %.2fs", elapsed)

        docs = result.get("source_documents", [])
        retrieved_text = " ".join(doc.page_content.lower() for doc in docs)
        question_terms = set(question.lower().split())
        match_score = sum(1 for word in question_terms if word in retrieved_text)

        logger.info("Match score: %s", match_score)

        if match_score < 2:
            fallback_msg = "Sorry, I couldn’t find anything in our Whirlpool manuals related to that."
            logger.info("Fallback response returned due to low match score")
            return fallback_msg

        final_answer = result["answer"] if args.verbose else distill_answer(result["answer"])
        logger.info("Final assistant response: %s", final_answer)
        return final_answer

    if args.chat:
        logger.info("Interactive chat mode started")
        print("=== Assistant Chat Mode === (Press Ctrl+C or type 'exit' to quit)")
        print("Assistant: Hi! I'm here to help with Whirlpool dishwashers. What’s the issue?")
        while True:
            try:
                q = input("[You]: ").strip()
                if q.lower() in {"exit", "quit"}:
                    logger.info("Session ended by user.")
                    print("Exiting chat. Goodbye!")
                    break
                response = respond(q)
                print("[Assistant]: ", response)
            except KeyboardInterrupt:
                logger.info("Session interrupted by user.")
                print("Exiting chat. Goodbye!")
                break
    elif args.query:
        logger.info("Single-query mode triggered: %s", args.query)
        print(f"[Assistant]: {respond(args.query)}")
    else:
        logger.warning("No query or chat flag provided.")
        print(f"Please provide either --query or --chat.")

if __name__ == "__main__":
    main()
