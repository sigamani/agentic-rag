from typing import Literal, Dict
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from pydantic import BaseModel
from langchain_core.runnables import Runnable

import json
import re

# Define the structured output format
class EvaluationResult(BaseModel):
    score: float
    explanation: str


# Updated evaluation prompt template
judge_accuracy_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an evaluation assistant. Only output a JSON object with:\n"
            '- "score": a float between 0.0 and 1.0\n'
            '- "explanation": a brief justification\n'
            "Respond with nothing else.",
        ),
        (
            "human",
            "Question: {question}\n\n"
            "Response: {response}\n\n"
            "Ground Truth: {ground_truth}",
        ),
    ]
)

judge_coherence_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are evaluating coherence in a multi-turn conversation. Only output a JSON object with:\n"
            '- "score": a float between 0.0 and 1.0\n'
            '- "explanation": a brief justification\n'
            "Respond with nothing else.",
        ),
        (
            "human",
            "Conversation History:\n{context}\n\n"
            "New Question: {question}\n\n"
            "Assistant Response: {response}",
        ),
    ]
)

# Use latest supported LLM interface
judge_model: Runnable = ChatOllama(model="mistral", temperature=0.0)


def _run_eval(prompt_template: str, variables: Dict) -> Dict:

    llm = ChatOllama(model="mistral")
    prompt = prompt_template.format(**variables)
    response = llm.invoke(prompt).content

    # Try direct JSON parse
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        pass

    # Try manually extracting score and explanation
    try:
        # Find score using regex
        score_match = re.search(r'"score"\s*:\s*(\d+(\.\d+)?)', response)
        explanation_match = re.search(r'"explanation"\s*:\s*"([^"]+)"', response, re.DOTALL)

        if score_match and explanation_match:
            return {
                "score": float(score_match.group(1)),
                "explanation": explanation_match.group(1)
            }

        raise ValueError("Could not parse fallback judge output.")
    except Exception as e:
        print("❌ Failed to parse judge response as JSON or fallback format:\n", response)
        raise e


def judge_accuracy(question: str, response: str, ground_truth: str) -> float:
    result = _run_eval(judge_accuracy_prompt, {
        "question": question,
        "response": response,
        "ground_truth": ground_truth,
    })
    return result["score"]


def judge_coherence(context: str, question: str, response: str) -> float:
    result = _run_eval(judge_coherence_prompt, {
        "context": context,
        "question": question,
        "response": response,
    })
    return result["score"]
