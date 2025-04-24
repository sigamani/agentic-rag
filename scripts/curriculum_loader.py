from datasets import Dataset


def merge_fields(example):
    return {
        **example,
        "text": f"""
    ### Instruction:
    {example.get('instruction', '')}

    ### Input:
    {example.get('input', '')}

    ### Response:
    {example.get('output', '')}
    """.strip()}


def load_and_split_dataset(path: str):
    import json

    def coerce_to_str_fields(example):
        return {
            k: " ".join(str(i) for i in v) if isinstance(v, list)
            else str(v) if v is not None
            else ""
            for k, v in example.items()
        }


    def classify_difficulty(example):
        program = example.get("Program", "").strip()
        if not program:
            return {"difficulty": "hard"}
        length = len(program.split())
        return {"difficulty": "easy" if length <= 5 else "medium"}

    # Load and clean
    with open(path, "r") as f:
        raw_data = [coerce_to_str_fields(json.loads(line)) for line in f if line.strip()]

    dataset = Dataset.from_list(raw_data)
    dataset = dataset.map(classify_difficulty)

    # Split based on difficulty label
    easy = dataset.filter(lambda x: x["difficulty"] == "easy")
    medium = dataset.filter(lambda x: x["difficulty"] == "medium")
    hard = dataset.filter(lambda x: x["difficulty"] == "hard")

    print(f"[\u2705 Data Loaded] Easy: {len(easy)} | Medium: {len(medium)} | Hard: {len(hard)}")


    easy = easy.map(merge_fields)
    medium = medium.map(merge_fields)
    hard = hard.map(merge_fields)

    return easy, medium, hard
