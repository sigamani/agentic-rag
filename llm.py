# Ollama
from openai import OpenAI

openai_api_key = "YOUR_API_KEY"
openai_api_base = "http://localhost:11434/v1"

llm = OpenAI(api_key=openai_api_key, base_url=openai_api_base)