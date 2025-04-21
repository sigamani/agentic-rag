from langchain_ollama import OllamaLLM
from langsmith import traceable
from langchain_core.messages import HumanMessage
 

MODEL_NAME = "hf.co/mradermacher/tat-llm-7b-fft-i1-GGUF:Q4_K_S"
# Initialize the model
llm = OllamaLLM(model=MODEL_NAME)


@traceable(name="LLM test call")
def call_llm(prompt: str):
    return llm.invoke(prompt)

if __name__ == "__main__":
    output = call_llm("Who was Kurt Cobain?")
    print(output)
