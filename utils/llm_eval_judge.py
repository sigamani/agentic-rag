import os
import json
import re
import anthropic
from langsmith import Client

# Setup clients
claude_client = anthropic.Anthropic(api_key=os.environ.get("CLAUDE_API_KEY"))
langsmith_client = Client()

# ---------------- Push segment to LangSmith ---------------- #
def push_segment_to_langsmith(segment, difficulty_label, dataset_name):
    dataset = next((ds for ds in langsmith_client.list_datasets() if ds.name == dataset_name), None)
    if not dataset:
        dataset = langsmith_client.create_dataset(dataset_name)

    for entry in segment:
        inputs = {
            "instruction": entry.get("instruction", ""),
            "input": entry.get("input", ""),
            "difficulty": difficulty_label
        }
        outputs = {
            "reasoning": entry.get("output", ""),
            "program": entry.get("Program", ""),
            "answer": str(entry.get("Final Answer", ""))
        }
        langsmith_client.create_example(inputs=inputs, outputs=outputs, dataset_id=dataset.id)



def score_flexible_final_answer(reasoning: str, final_answer: str) -> float:
    """
    Uses Claude to score whether the reasoning and final answer are logically sound.
    Returns 1.0, 0.5, or 0.0 based on human-style judgment.
    """
    prompt = f"""
    You are an expert tutor evaluating a student's financial reasoning.
    
    They were asked to solve a financial question and gave the following explanation and final answer.
    
    Please judge with empathy — this student is learning, so small errors in formatting or rounding are acceptable.
    
    Use the following rubric:
    - 1.0 = Final answer is correct or acceptably close; reasoning is sound and complete.
    - 0.5 = Reasoning is partially correct; logic mostly works, some flaws.
    - 0.0 = Reasoning is incorrect or final answer is clearly wrong.
    
    Respond ONLY with a numeric score: 1.0, 0.5, or 0.0 — no explanation.
    
    ---
    
    Reasoning:
    {reasoning}
    
    Final Answer (as claimed by the student):
    {final_answer}
    
    Score:
    """

    try:
        response = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=5,
            temperature=0,
            messages=[{"role": "user", "content": prompt}],
        )

        content = response.content[0].text.strip()
        match = re.search(r"\b(1\.0|0\.5|0\.0|1|0)\b", content)
        if match:
            return float(match.group(1))
        else:
            print(f"[Claude Eval Warning] Unexpected response: {content}")
            return 0.0

    except Exception as e:
        print(f"[Claude Eval Error] {e}")
        return 0.0


def evaluate_final_answer_accuracy(dataset, sample_size=100):
    """
    Runs Claude evaluation on a sample of the dataset.
    Returns average score and individual examples (for optional logging).
    """
    print("[__ Claude Evaluation] Scoring reasoning quality on subset...")
    subset = dataset.select(range(min(sample_size, len(dataset))))
    results = []
    examples = []

    for ex in subset:
        reasoning = ex.get("output", "")
        answer = str(ex.get("Final Answer", ""))
        score = score_flexible_final_answer(reasoning, answer)
        results.append(score)
        examples.append({
            "question": ex.get("input", ""),
            "model_reasoning": reasoning,
            "final_answer": answer,
            "score": score
        })

    avg_score = sum(results) / len(results) if results else 0.0
    print(f"[__ Claude Score]: {avg_score:.3f} over {len(results)} examples")
    return avg_score, examples
