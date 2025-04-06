from langsmith import Client

client = Client()

dataset_name = "agentic-troubleshooting"
print(f"Uploading multiturn examples to dataset: {dataset_name}")

multiturn_examples = [
    {
        "inputs": {
            "question": "It works now! Thanks.",
            "conversation": (
                "Technician: I’m having trouble with a Model 18 ADA dishwasher. It’s showing an error code E4 and isn’t draining.\n"
                "Technician: I’ve checked the hose and it’s clear.\n"
                "Technician: There’s some debris in the pump. I’ve cleaned it."
            ),
        },
        "outputs": {
            "answer": "Glad to hear it's working now. Let me know if anything else comes up."
        },
        "metadata": {
            "expected_sources": ["whirlpool_local", "whirlpool_online"],
            "expected_keywords": ["drain", "pump", "resolved"]
        },
    },
    {
        "inputs": {
            "question": "It doesn’t seem to be starting the test.",
            "conversation": (
                "Technician: How do I run diagnostics on an LG dishwasher?\n"
                "Technician: Do I need to press anything else after that?"
            ),
        },
        "outputs": {
            "answer": "Hold the start and delay buttons together until the display flashes."
        },
        "metadata": {
            "expected_sources": ["lg_owner_manual"],
            "expected_keywords": ["diagnostic", "start button", "test mode"]
        },
    }
]

for example in multiturn_examples:
    client.create_example(
        dataset_name=dataset_name,
        inputs=example["inputs"],
        outputs=example["outputs"],
        metadata=example["metadata"]
    )

print("✅ Done uploading multi-turn benchmark examples to LangSmith.")
