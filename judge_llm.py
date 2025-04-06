from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# You can swap in another LLM here (e.g., OpenAI or Claude)
judge_llm = ChatOllama(model="mistral", temperature=0.0)

judge_prompt = ChatPromptTemplate.from_template("""
You are a helpful and strict evaluation assistant.

Given:
- A technician query
- The assistant's response
- A golden reference answer

Evaluate the assistant's response on a scale from 0 to 1:
- 1 = fully correct and contextually grounded
- 0 = completely incorrect or hallucinated

Be concise. Justify your score briefly.

### Technician Query:
{question}

### Assistant Response:
{response}

### Reference Answer:
{reference}

Score (0–1) and justification:
""")

coherence_prompt = ChatPromptTemplate.from_template("""
You are a helpful assistant evaluating context coherence.

Given:
- The technician's query
- The assistant's response
- The retrieved document context

Score how well the assistant's answer aligns with and utilises the context.

### Score Guide ###
- 1 = Fully coherent with context and relevant to query
- 0 = Incoherent or unrelated to context
- Justify your score in 1-2 sentences.

### Technician Query:
{question}

### Assistant Response:
{response}

### Retrieved Context:
{context}

Score (0–1) and justification:
""")

coherence_chain = coherence_prompt | judge_llm | StrOutputParser()

def judge_coherence(question, response, context):
    result = coherence_chain.invoke({
        "question": question,
        "response": response,
        "context": context
    })
    try:
        score_str = result.split("Score")[1].split(":")[1].strip().split()[0]
        return float(score_str)
    except Exception:
        return 0.0

judge_chain = judge_prompt | judge_llm | StrOutputParser()

def judge_accuracy(question, response, reference):
    result = judge_chain.invoke({
        "question": question,
        "response": response,
        "reference": reference
    })

    try:
        score_str = result.split("Score")[1].split(":")[1].strip().split()[0]
        return float(score_str)
    except Exception:
        return 0.0
