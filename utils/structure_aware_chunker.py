
import tiktoken
import json
import re
import textwrap
from typing import List, Dict
from datetime import datetime
from langchain_ollama import ChatOllama
from langchain.prompts import PromptTemplate
from langchain.docstore.document import Document
from pathlib import Path

MODEL = "mistral"
ENCODING = "gpt2"
MAX_CHUNK_TOKENS = 256
DEBUG_LOG_DIR = "data/debug_llm_responses"
FAILURE_LOG = "data/failures.jsonl"

enc = tiktoken.get_encoding(ENCODING)

def count_tokens(text: str) -> int:
    return len(enc.encode(text))

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def safe_json_load(text: str, page: int) -> List[Dict]:
    Path(DEBUG_LOG_DIR).mkdir(parents=True, exist_ok=True)
    debug_file = Path(DEBUG_LOG_DIR) / f"debug_llm_response_page{page}.txt"
    debug_file.write_text(text or "[EMPTY RESPONSE]")

    try:
        cleaned = textwrap.dedent(text).strip()
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        log(f"[Sanitising] JSON failed: {e}")
        print(f"[Snippet] {text[:300].replace(chr(10), ' ')}")
        cleaned = re.sub(r"[\x00-\x1F\x7F]", "", text)
        try:
            cleaned = textwrap.dedent(cleaned).strip()
            return json.loads(cleaned)
        except json.JSONDecodeError as e2:
            log(f"[Final Fail] Still invalid JSON: {e2}")
            with open(FAILURE_LOG, "a") as f:
                json.dump({
                    "page": page,
                    "error": str(e2),
                    "raw": cleaned[:1000]
                }, f)
                f.write("\n")
            return []

class StructureAwareChunker:
    def __init__(self, model_name=MODEL, debug=False):
        self.llm = ChatOllama(model=model_name, temperature=0.2, max_tokens=512)
        self.debug = debug

    def chunk(self, text: str, page: int = None, title: str = None) -> List[Document]:
        log(f"→ Structure-aware LLM chunking (page {page}, title={title})...")

        few_shot_example = """
Example:
[
  {
    "text": "Ensure the dishwasher is connected to a grounded electrical outlet.",
    "entities": [{"name": "dishwasher", "type": "device"}, {"name": "electrical outlet", "type": "component"}],
    "steps": ["Connect dishwasher to grounded outlet"],
    "links_to": ["Installation > Electrical"],
    "category": "Installation"
  }
]
"""

        prompt_template = PromptTemplate.from_template("""
You are an expert document analyst and structured information extractor.

Given a raw technical manual section, split it into clean, sentence-complete chunks (≤ 256 tokens) and enrich each with metadata.

Each chunk MUST include:
- "text": full cleaned sentence(s) (always present)
- "entities": list of domain-specific terms (device, part, error_code, unit, action)
- "steps": list of inferred user/technician actions (even if implied)
- "links_to": inferred headings or sections — always include: "{title}"
- "category": high-level classifier (e.g., Overview, Installation, Safety, Troubleshooting)

Respond strictly in this JSON format:
{few_shot}

Section:
{text}
""")

        response = self.llm.invoke(prompt_template.format(text=text, few_shot=few_shot_example, title=title)).content
        parsed_blocks = safe_json_load(response, page)

        results = []
        for parts in parsed_blocks:
            links = parts.get("links_to", [])
            if title and title not in links:
                links.append(title)

            doc = Document(
                page_content=parts.get("text", ""),
                metadata={
                    "entities": parts.get("entities", []),
                    "steps": parts.get("steps", []),
                    "links_to": links,
                    "category": parts.get("category", "Unclassified"),
                    "source_page": page,
                    "source_title": title,
                    "source_paragraph": text
                }
            )

            if self.debug:
                print("=" * 80)
                print(doc.page_content)
                print(doc.metadata)

            if count_tokens(doc.page_content) <= MAX_CHUNK_TOKENS:
                results.append(doc)

        log(f"← {len(results)} structure-aware chunks returned.")
        return results
