
import json
import re
from typing import Literal, TypedDict, Annotated, Sequence
from langchain_chroma import Chroma
from langgraph.graph import StateGraph, add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.documents import Document
from langchain.prompts import PromptTemplate
from operator import add

from tqdm.auto import tqdm

from openai import OpenAI

def format_document(entry: dict) -> Document:
    # Combine pre_text, post_text, and table content into a single text block
    combined_text = ""
    
    combined_text += "\n".join(entry['pre_text'])
    
    # Process the table to include in the text block
    table_text = []
    for row in entry['table']:
        # Join each cell in the row with a tab for clarity
        table_text.append("\t".join(row))

    table_text = "\n".join(table_text)

    combined_text += "\n\n" + table_text
    combined_text += "\n\n" + "\n".join(entry['post_text'])
    
    # Combine all text and table data
    full_text = combined_text + "\n\n" + "Table Data:\n" + table_text
    
    return Document(id=entry['id'], page_content=full_text, metadata={"qa": str(entry.get('qa'))})
    
def create_question_to_document_map(filepath: str, limit: int = None):
    q2d = {}

    with open(filepath, 'r') as f:
        data = json.load(f)
    
    QA_FIELDS = ["qa", *[f"qa_{i}" for i in range(10)]]
    if limit:
        data = data[:limit]

    for entry in tqdm(data):
        # Loop through every available QA field in the entry
        for qa_field in set(QA_FIELDS).intersection(entry.keys()):
            q2d[entry[qa_field]["question"]] = format_document(entry)
  
    return q2d