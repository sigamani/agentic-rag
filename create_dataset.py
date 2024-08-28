import json
from langchain_core.documents import Document
from tqdm.auto import tqdm
from langfuse_config import langfuse
from config import DATA_PATH, DATA_LIMIT_EVAL, LANGFUSE_DATASET_NAME

def create_convfinqa_langfuse_dataset(filepath, name, description, limit: int = None) -> list[Document]:
    langfuse.create_dataset(name=name, description=description)
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    QA_FIELDS = ["qa", *[f"qa_{i}" for i in range(10)]]
    SKIPPED_METADATA_FIELDS = ['annotation', *QA_FIELDS]
    if limit:
        data = data[:limit]

    for entry in tqdm(data):
        # Loop through every available QA field in the entry
        for qa_field in set(QA_FIELDS).intersection(entry.keys()):
            # Upload to Langfuse
            langfuse.create_dataset_item(
                dataset_name=name,
                # any python object or value
                input=entry[qa_field]["question"],
                # any python object or value, optional
                expected_output=entry[qa_field]["answer"],
                metadata={
                    "document": {field: entry[field] for field in entry.keys() if field not in SKIPPED_METADATA_FIELDS},
                }
            )

create_convfinqa_langfuse_dataset(DATA_PATH, LANGFUSE_DATASET_NAME, "Dataset created from ConvFinQA train data", limit=DATA_LIMIT_EVAL)


