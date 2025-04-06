import json
from typing import Literal

from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from pydantic import BaseModel
from langchain_core.runnables import Runnable


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


def _run_eval(prompt_template: ChatPromptTemplate, input_map: dict) -> EvaluationResult:
    prompt = prompt_template.format(**input_map)
    response = judge_model.invoke(prompt)

    try:
        # Ensure we only extract the JSON portion (if extra text exists)
        content = response.content.strip()

        # Try to extract the JSON object via regex if full parse fails
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            import re

            # Match first valid-looking JSON object
            match = re.search(r'\{\s*"score"\s*:\s*[0-9.]+,\s*"explanation"\s*:\s*".+?"\s*\}', content, re.DOTALL)
            if match:
                parsed = json.loads(match.group())
            else:
                raise ValueError("No valid JSON object found in response")

        return EvaluationResult(**parsed)

    except Exception as e:
        print("❌ Failed to parse judge response as JSON:\n", response.content)
        raise e

def judge_accuracy(question: str, response: str, ground_truth: str) -> float:
    result = _run_eval(judge_accuracy_prompt, {
        "question": question,
        "response": response,
        "ground_truth": ground_truth,
    })
    return result.score


def judge_coherence(context: str, question: str, response: str) -> float:
    result = _run_eval(judge_coherence_prompt, {
        "context": context,
        "question": question,
        "response": response,
    })
    return result.score
