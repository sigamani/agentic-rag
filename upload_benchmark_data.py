import os
from langsmith import Client

client = Client()

DATASET_NAME = "agentic-troubleshooting"

examples = [
    {
        "inputs": {
            "question": "I’m having trouble with a Model 18 ADA dishwasher. It’s showing an error code E4 and isn’t draining.",
            "conversation": "",
        },
        "outputs": {"output": "Check drain hose for blockages or kinks. If clear, inspect the drain pump."},
    },
    {
        "inputs": {
            "question": "I’ve checked the hose and it’s clear.",
            "conversation": "Technician: I’m having trouble with a Model 18 ADA dishwasher. It’s showing an error code E4 and isn’t draining.\nAI Assistant: Check drain hose for blockages or kinks. If clear, inspect the drain pump.",
        },
        "outputs": {"output": "Next, check the drain pump for debris or mechanical failure."},
    },
    {
        "inputs": {
            "question": "What does E4.1 mean on a Tesla dishwasher?",
            "conversation": "",
        },
        "outputs": {"output": "E4.1 typically indicates an overflow issue caused by water reaching the base of the dishwasher."},
    },
    {
        "inputs": {
            "question": "How do I run diagnostics on an LG dishwasher?",
            "conversation": "",
        },
        "outputs": {"output": "Hold the start and delay buttons simultaneously for 3 seconds to enter diagnostic mode."},
    },
    {
        "inputs": {
            "question": "How should I load cutlery in a Miele G6100 dishwasher?",
            "conversation": "",
        },
        "outputs": {"output": "Place cutlery in the top tray with handles down, separating items to ensure water flow."},
    },
]

# Upload to LangSmith
print(f"Uploading examples to dataset: {DATASET_NAME}")
for example in examples:
    client.create_example(
        dataset_name=DATASET_NAME,
        inputs=example["inputs"],
        outputs=example["outputs"],
    )
print("✅ Done uploading benchmark data to LangSmith.")
