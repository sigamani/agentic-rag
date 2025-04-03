from rich import print
from langchain_community.docstore.document import Document
from langchain_community.chat_models import ChatOllama
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community import embeddings
from langchain_core.runnables.passthrough import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

local_llama = ChatOllama(model="mistral")
OPENAI_API_KEY = "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"


def rag(chunks, collection_name):
    vectorstore = Chroma.from_documents(
        documents=documents,
        collection_name=collection_name,
        embedding=OllamaEmbeddings(model="nomic-embed-text"),
    )

    retriever = vectorstore.as_retriever()

    prompt_template = """
    Answer the question based only on the followeing context:
    {context} 
    Question: {question}
    """

    prompt = ChatPromptTemplate.from_template(prompt_template)

    chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | local_llama
        | StrOutputParser()
    )

    result = chain.invoke(
        """I’m having trouble with a Model 18 ADA dishwasher. 
                             It’s showing an error code E4 and the customer 
                             is complaining is it not draining?
                             """
    )
    print(result)


# 1. Character Text Splitting
print("### Character Text Splitting ###")

text = "Text splitting in LangChain is a critical feature. -Users can leverage LangChain for text splitting. -LangChain allows users to efficiently navigate and analyze vast amounts of text data. -Text splitting with LangChain facilitates a deeper understanding and more insightful conclusions"

# 2. Manual splitting
chunks = []
chunk_size = 35

for i in range(0, len(text), chunk_size):
    chunk = text[i : i + chunk_size]
    chunks.append(chunk)
documents = [
    Document(page_content=chunk, metadata={"source": "local"}) for chunk in chunks
]

print(documents)

# 3. Automatic Text Splitting
print("### Automatic Text Splitting ###")

from langchain.text_splitter import CharacterTextSplitter

text_splitter = CharacterTextSplitter(
    chunk_size=35, chunk_overlap=0, separator="", strip_whitespace=False
)

documents = text_splitter.create_documents([text])

print(documents)


# 4. Recursive Text Splitting
print("### Recursive Text Splitting ###")

from langchain.text_splitter import RecursiveCharacterTextSplitter

with open("content.txt", "r", encoding="utf-8") as file:

    text = file.read()

text_splitter = CharacterTextSplitter(chunk_size=65, chunk_overlap=0)

documents = text_splitter.create_documents([text])
print(documents)


# 5. Semantic chunking
print("### Semantic Chunking ###")

from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai.embeddings import OpenAIEmbeddings

text_splitter = SemanticChunker(
    OpenAIEmbeddings(), breakpoint_threshold_type="percentile"
)

documents = text_splitter.create_documents([text])

# print(documents)
# rag(documents, "semantic-chunks")

# 6. Agentic Chunking
print("### Agentic Chunking ###")

from langchain_openai import ChatOpenAI
from typing import Optional, List
from pydantic import BaseModel, Field
from langchain import hub
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain.chains import create_extraction_chain_pydantic

prompt_template = hub.pull("wfh/proposal-indexing")
llm = ChatOpenAI(model="gpt-4")
runnable = prompt_template | llm


class Sentences(BaseModel):
    sentences: List[str] = Field(
        description="The list of key sentence-level propositions"
    )


extraction_chain = create_extraction_chain_pydantic(pydantic_schema=Sentences, llm=llm)


# Modern replacement for extraction_chain
# extraction_chain = llm.with_structured_output(Sentences)
extraction_chain = llm.with_structured_output(Sentences, method="function_calling")

# Usage
parsed = extraction_chain.invoke("LangChain is a framework for LLMs.")
print(parsed.sentences)


def get_propositions(text):
    runnable_output = runnable.invoke({"input": text}).content
    propositions = extraction_chain.invoke(runnable_output)
    return propositions.sentences


paragraphs = text.split("\n")
text_propositions = []
for i, para in enumerate(paragraphs[:5]):
    propositions = get_propositions(para)
    text_propositions.extend(propositions)
    print(f"Done with {i}")

print(f"You have {len(text_propositions)}")
print(text_propositions[:10])

print("### Group Chunk")

from agentic_chunker import AgenticChunker

ac = AgenticChunker()
ac.add_propositions(text_propositions)

chunks = ac.get_chunks(get_type="list_of_strings")
documents = [
    Document(page_content=chunk, metadata={"source": "local"}) for chunk in chunks
]

print(documents)
print(chunks)

rag(documents, "agentic-chunks")
