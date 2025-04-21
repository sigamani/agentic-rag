from langchain_ollama import OllamaLLM
from langsmith import traceable
from langchain_core.messages import HumanMessage

# Initialize the model with the name you used during creation
llm = OllamaLLM(model="hf.co/mradermacher/tat-llm-7b-fft-i1-GGUF:Q4_K_M")

@traceable(name="LLM test call")
def call_llm(prompt: str):
    return llm.invoke([HumanMessage(content=prompt)])

if __name__ == "__main__":
    output = call_llm("Hello World")
    print(output)
