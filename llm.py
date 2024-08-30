# Ollama
from langfuse.openai import OpenAI
import os
import dotenv

dotenv.load_dotenv()

# We're using OpenAI API compatible format, so we can use OpenAI SDK to interact with our LLM
LLM_API_KEY = os.getenv("LLM_API_KEY", "API_KEY")
LLM_API_BASE = os.getenv("LLM_API_BASE", "http://localhost:8000/v1")
MODEL_NAME = os.getenv("LLM_MODEL", "llama3.1")
llm = OpenAI(api_key=LLM_API_KEY, base_url=LLM_API_BASE)

if __name__ == "__main__":
    out = llm.completions.create(model=MODEL_NAME, prompt="Hello World", max_tokens=10)

    print(out)
