import os
from langsmith import Client
from langsmith.schemas import Example
from langsmith import Client
from run_agent import build_rag_chain, load_and_chunk_documents


DATASET_NAME = "agentic-troubleshooting"

# You can replace "gpt-4" with another model if needed
JUDGE_MODEL = "gpt-4"

# Run evaluation
print(f"🔍 Evaluating dataset: {DATASET_NAME} with LLM judge {JUDGE_MODEL}...")


client = Client()
documents = load_and_chunk_documents()
chain = build_rag_chain(documents)

# Use evaluate method on a dataset
client.run_on_dataset(
    dataset_name="agentic-troubleshooting",
    llm_or_chain_factory=lambda: chain,
    evaluation_steps=["qa", "criteria"],
    criteria=["conciseness", "relevance", "correctness"],
    experiment_prefix="eval-batch",
)
