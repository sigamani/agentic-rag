import json
from langsmith import Client
from langsmith.schemas import Example

def populate_dataset_from_jsonl(dataset_name, jsonl_path):
    client = Client()

    dataset = next((ds for ds in client.list_datasets() if ds.name == dataset_name), None)
    if not dataset:
        dataset = client.create_dataset(dataset_name)

    with open(jsonl_path, 'r') as f:
        for line in f:
            record = json.loads(line)
            client.create_example(
                inputs={
                    "question": record["question"],
                    "context": record["context"],
                    "table": record.get("table", "")
                },
                outputs={
                    "answer": record["answer"],
                    "reasoning": record.get("reasoning", ""),
                    "program": record.get("program", "")
                },
                dataset_id=dataset.id
            )

if __name__ == "__main__":
    populate_dataset_from_jsonl(
        dataset_name="convfinqa-finetune-eval",
        jsonl_path="data/train_curated"
    )
