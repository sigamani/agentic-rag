from typing import TypedDict
from langchain_core.documents import Document

from config import GraphConfig

import re

def extract_numbers(text):
    """Extracts all numeric values from a string and returns them as a set of strings."""
    return set(re.findall(r"\\d+(?:\\.\\d+)?", text))

def format_document(entry: dict) -> Document:
    """
    Combine pre_text, post_text, and table content into a single text block.

    HTML is a decent way to represent tables.

    References:
        - Study that shows GPT4 performs performs best with HTML: https://arxiv.org/html/2305.13062v4
        - Discussion where a few people mentioned they had the best results with HTML: https://news.ycombinator.com/item?id=41043771
    """
    # Combine pre_text, post_text, and table content into a single text block
    combined_text = ""

    combined_text += "\n".join(entry["pre_text"])

    # Process the table to include in the text block as HTML
    table_html = "<table>\n"
    for row in entry["table"]:
        table_html += "  <tr>\n"
        for cell in row:
            table_html += f"    <td>{cell}</td>\n"
        table_html += "  </tr>\n"
    table_html += "</table>"

    combined_text += "\n\n" + table_html
    combined_text += "\n\n" + "\n".join(entry["post_text"])

    # Combine all text and table data
    full_text = combined_text + "\n\n" + "Table Data:\n" + table_html

    return Document(
        id=entry["id"],
        page_content=full_text,
        metadata={"id": entry["id"], "qa": str(entry.get("qa"))},
    )


# Apply Llama3.1 chat-template
def format_prompt(user_query: str):
    """
    Apply Llama3.1 chat-template.

    Args:
        user_query (str): The user query.

    References:
        - Llama3.1 chat-template: https://llama.meta.com/docs/model-cards-and-prompt-formats/llama3_1
    """
    template = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\nYou are a helpful assistant.<|eot_id|><|start_header_id|>user<|end_header_id|>\n\n{}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"""
    return template.format(user_query)

def typed_dict_to_dict(x) -> dict:
    return {k: v for k, v in x.__dict__.items() if not k.startswith('__')}
