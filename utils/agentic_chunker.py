import tiktoken
from typing import List, Dict
from langchain_ollama import ChatOllama
from langchain.prompts import PromptTemplate

# Config
MODEL = "mistral"
MAX_CHUNK_TOKENS = 256
ENCODING = "gpt2"

enc = tiktoken.get_encoding(ENCODING)


def count_tokens(text: str) -> int:
    return len(enc.encode(text))


def split_with_llm(text: str, page: int = None, title: str = None) -> List[Dict]:
    system_prompt = (
        "Split the following technical manual section into semantically meaningful, self-contained chunks.\n"
        "Each chunk should:\n"
        "- Be no longer than 256 tokens.\n"
        "- Never break mid-sentence.\n"
        "- Represent a single step, operation, or idea.\n"
        "- Exclude pure headings or labels with no content.\n"
        "- Ignore chunks that are trivial (e.g. model numbers or isolated codes).\n"
        "- Normalise curly quotes to straight quotes.\n\n"
        "Output the chunks as a numbered list. Do not include commentary or titles.\n\n"
        "Manual Section:\n{text}"
    )

    llm = ChatOllama(model=MODEL, temperature=0.2, max_tokens=1024)
    prompt = PromptTemplate.from_template(system_prompt)
    response = llm.invoke(prompt.format(text=text)).content

    chunks = []
    for line in response.strip().split("\n"):
        if line.strip() and line[0].isdigit():
            content = line.split(".", 1)[-1].strip()
            if count_tokens(content) <= MAX_CHUNK_TOKENS:
                chunks.append(
                    {
                        "text": content,
                        "metadata": {
                            "source_page": page,
                            "source_title": title,
                            "source_paragraph": text,
                        },
                    }
                )
    return chunks
