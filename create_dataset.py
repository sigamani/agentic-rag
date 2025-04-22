import json
import re
from datetime import datetime
from dateutil import parser as date_parser
from pathlib import Path

indexed_data_object = {}
description_store = {}
metadata_object = {}

# --- Helpers ---
def normalize_scientific(value):
    try:
        num = float(value.replace(",", "").replace("$", "").replace("%", ""))
        return f"{num:.2E}"
    except Exception:
        return value

def normalize_time(raw_time):
    try:
        if "Q1" in raw_time:
            return int(datetime.strptime(raw_time[:4] + "-01-01", "%Y-%m-%d").timestamp())
        elif "Q2" in raw_time:
            return int(datetime.strptime(raw_time[:4] + "-04-01", "%Y-%m-%d").timestamp())
        elif "Q3" in raw_time:
            return int(datetime.strptime(raw_time[:4] + "-07-01", "%Y-%m-%d").timestamp())
        elif "Q4" in raw_time:
            return int(datetime.strptime(raw_time[:4] + "-10-01", "%Y-%m-%d").timestamp())
        else:
            return int(date_parser.parse(raw_time).timestamp())
    except Exception:
        return 0

def infer_unit(cell, context_text):
    if "$" in cell or "dollar" in context_text.lower():
        return "USD"
    elif "%" in cell or "percent" in context_text.lower():
        return "%"
    elif "eps" in context_text.lower():
        return "EPS"
    elif "margin" in context_text.lower():
        return "Margin"
    return "N/A"

def extract_description_tagged(entry):
    ori = entry.get("table_ori", "")
    if isinstance(ori, str):
        raw = ori
    elif isinstance(ori, list):
        raw = " ".join(
            item if isinstance(item, str) else " ".join(sub for sub in item if isinstance(sub, str))
            for item in ori
        )
    else:
        raw = ""
    cleaned = re.sub(r"\$?\d+[\d,.]*%?", "", raw)
    cleaned = re.sub(r"\b(billion|million|usd|eps|percent|cents|dollars)\b", "", cleaned, flags=re.I)
    phrases = re.split(r"\s{2,}|(?<=[a-z])\.\s+|(?<=[a-z]):\s+|(?<=\w)\s{1,}(?=\w)", cleaned)
    tag_wrapped = " ".join(f"<TAG> {p.strip()} </TAG>" for p in phrases if p.strip())
    return tag_wrapped.strip().lower()

# --- Main Processing Function ---
def process_table_data(dataset):
    for entry in dataset:
        table_id = entry["id"]
        table = entry.get("table", [])
        pre = entry.get("pre_text", entry.get("paragraph", ""))
        post = entry.get("post_text", "")
        desc = extract_description_tagged(entry)

        metadata_object[table_id] = re.split(r"[.?!]\s*", f"{pre} {post}")

        if table and len(table) > 1:
            header = table[0]
            for i, row in enumerate(table[1:], 1):
                if len(row) != len(header):
                    continue
                for j, cell in enumerate(row):
                    value = normalize_scientific(cell)
                    date_label = next((r for r in row if re.search(r"20\\d{2}|Q[1-4]", r)), "2020")
                    timestamp = normalize_time(date_label)
                    field_id = f"{table_id}-Row{i}-{header[j].strip()}"

                    indexed_data_object[field_id] = {
                        "value": value,
                        "unit": infer_unit(cell, pre + post),
                        "date": timestamp
                    }
                    description_store[field_id] = desc

with open("data/train.json", "r") as f:
    dataset = json.load(f)
    process_table_data(dataset)

with open("indexed_data_object.json", "w") as f:
    json.dump(indexed_data_object, f, indent=2)

with open("description_store.json", "w") as f:
    json.dump(description_store, f, indent=2)

with open("metadata_object.json", "w") as f:
    json.dump(metadata_object, f, indent=2)
