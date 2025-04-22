# llm_parse_table.py

import json
from pathlib import Path
from langchain_ollama import OllamaLLM
from tqdm import tqdm

llm = OllamaLLM(model="mistral")

def format_prompt(entry):
    doc_id = entry.get("id", "")
    pre_text = entry.get("pre_text", "")
    post_text = entry.get("post_text", "")
    table = entry.get("table_ori", entry.get("table", []))
    date = entry.get("paragraph", "") or "Unknown Date"
    table_str = json.dumps(table, indent=2)

    return f"""You are an information extraction agent.

    Given a financial table and context, extract each value into a structured JSON object with the following keys:
    - id: "<sluggified doc_id and row_number>"
    - name: "<field_name>"
    - value: "<scientific_notation_float>"
    - type: "float"
    - unit: "currency"
    - date: "{date}"
    - row: <int>
    - description: "A summary based on pre_text and post_text"
    - metadata: Relevant text from pre_text and post_text which are linked to the numeric values in the tables

    Respond with a JSON array of objects, one per data value.

    Context:
    - ID: {doc_id}
    - Pre-text: "{pre_text}"
    - Post-text: "{post_text}"
    - Date: "{date}"

Table:
{table_str}
"""

def main(input_path, output_path, max_examples=5):
    with open(input_path, 'r') as f:
        data = json.load(f)

    results = []
    for entry in tqdm(data[:max_examples], desc="Processing examples"):
        prompt = format_prompt(entry)
        response = llm.invoke(prompt)
        try:
            parsed = json.loads(response)
            results.append({
                "id": entry["id"],
                "extracted": parsed
            })
        except Exception as e:
            results.append({
                "id": entry["id"],
                "error": str(e),
                "raw_response": response
            })

    with open(output_path, 'w') as f:
        for r in results:
            f.write(json.dumps(r) + "\n")
    print(f"✅ Saved {len(results)} entries to {output_path}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_file", type=str, required=True)
    parser.add_argument("--output_file", type=str, default="llm_extracted_results.jsonl")
    parser.add_argument("--max_examples", type=int, default=5)
    args = parser.parse_args()
    main(args.input_file, args.output_file, args.max_examples)

