from langchain_together import ChatTogether
import os
from langsmith import traceable
from langchain_ollama import OllamaLLM

# Initialize the model
llm = OllamaLLM(model="hf.co/mradermacher/tat-llm-7b-fft-i1-GGUF:Q4_K_M")

# Hardcoded Together AI configuration
#LLM_API_KEY = "f2ca76b85d77e125667559d3bbb282901dbb80d89af2f9831e6de303a532a2f0"
#LLM_API_BASE = "https://api.together.xyz/v1"
#MODEL_NAME = "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"

if __name__ == "__main__":
    from langchain_core.messages import HumanMessage

    @traceable(name="LLM test call")
    def call_llm(prompt: str):
        return llm.invoke([HumanMessage(content=prompt)])

    output = call_llm("Hello World")
    print(output)
