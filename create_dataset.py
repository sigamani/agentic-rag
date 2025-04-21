import json
import re
from pathlib import Path
from tqdm.auto import tqdm
from datasets import Dataset

def difficulty_tag(program):
    if not program:
        return "unknown"
    if len(program) <= 3:
        return "easy"
    elif any(op in program for op in ["max", "min", "div"]):
        return "hard"
    elif len(program) > 5:
        return "medium"
    return "easy"

def tag_numerical_tokens(text):
    text = re.sub(r"\$\s?([\d,.]+)", r"<CURRENCY> \1 </CURRENCY>", text)
    text = re.sub(r"([\d,.]+)%", r"<PERCENT> \1 </PERCENT>", text)
    text = re.sub(r"(?<!\$)(?<!%)\b([\d,.]+)\b", r"<NUMBER> \1 </NUMBER>", text)
    return text

def summarize_table(text):
    if not text:
        return ""
    lines = text.splitlines()
    numeric_lines = [line for line in lines if any(char.isdigit() for char in line)]
    return f"Summary: {len(numeric_lines)} rows of numeric data present. Headers include: {lines[0] if lines else ''}".strip()

def create_convfinqa_hf_dataset(filepath: str, output_path: str, limit: int = None, multiturn: bool = False) -> None:
    with open(filepath, 'r') as f:
        data = json.load(f)

    if limit:
        data = data[:limit]

    hf_data = []

    if multiturn:
        for ex in tqdm(data, desc="Processing multi-turn examples"):
            history = ex.get("history", [])
            question = ex.get("question", "")
            answer = ex.get("answer", "")
            program = ex.get("program", [])
            table = ex.get("table", "")

            conversation = "\n".join([f"Q: {q}\nA: {a}" for q, a in history] + [f"Q: {question}"])
            tagged_convo = tag_numerical_tokens(conversation)
            tagged_answer = tag_numerical_tokens(answer)
            table_summary = summarize_table(table)

            full_input = f"<CONTEXT> {table_summary} </CONTEXT>\n\n<CONVERSATION>\n{tagged_convo}\n</CONVERSATION>"

            hf_data.append({
                "input": full_input,
                "output": tagged_answer,
                "metadata": {
                    "question_id": ex.get("question_id", ""),
                    "program": program,
                    "difficulty": difficulty_tag(program)
                }
            })
    else:
        QA_FIELDS = ["qa"] + [f"qa_{i}" for i in range(10)]
        SKIPPED_METADATA_FIELDS = ['annotation', *QA_FIELDS]

        for entry in tqdm(data, desc="Processing single-turn examples"):
            table = entry.get("table", "")
            table_summary = summarize_table(table)

            for qa_field in set(QA_FIELDS).intersection(entry.keys()):
                qa = entry[qa_field]
                question = qa.get("question", "")
                answer = qa.get("answer", "")
                program = qa.get("program", [])

                tagged_question = tag_numerical_tokens(question)
                tagged_answer = tag_numerical_tokens(answer)

                full_input = f"<CONTEXT> {table_summary} </CONTEXT>\n\n<QUESTION> {tagged_question} </QUESTION>"

                hf_data.append({
                    "input": full_input,
                    "output": tagged_answer,
                    "metadata": {
                        "document": {field: entry[field] for field in entry if field not in SKIPPED_METADATA_FIELDS},
                        "qa_field": qa_field,
                        "program": program,
                        "difficulty": difficulty_tag(program)
                    }
                })

    with open(output_path + ".jsonl", "w") as f:
        for item in hf_data:
            f.write(json.dumps(item) + "\n")

    print(f"✅ Saved tokenizer-ready JSONL: {output_path}.jsonl")
    return hf_data

def convert_to_tokenizer_friendly(path_in: str, path_out_base: str):
    with open(path_in, "r") as f:
        data = [json.loads(line) for line in f]
    ds = Dataset.from_list(data)
    ds.to_json(f"{path_out_base}.json")
    ds.to_parquet(f"{path_out_base}.parquet")
    ds.save_to_disk(f"{path_out_base}_hf_dataset")
    print(f"✅ Saved HF dataset to: {path_out_base}.json, .parquet, and _hf_dataset")

if __name__ == "__main__":
    single = create_convfinqa_hf_dataset(
        filepath="data/train.json",
        output_path="data/hf_convfinqa_single_turn",
        limit=100,
        multiturn=False
    )
    convert_to_tokenizer_friendly("data/hf_convfinqa_single_turn.jsonl", "data/hf_convfinqa_single_turn")

    multi = create_convfinqa_hf_dataset(
        filepath="data/dev_turn.json",
        output_path="data/hf_convfinqa_multi_turn",
        limit=None,
        multiturn=True
    )
    convert_to_tokenizer_friendly("data/hf_convfinqa_multi_turn.jsonl", "data/hf_convfinqa_multi_turn")
