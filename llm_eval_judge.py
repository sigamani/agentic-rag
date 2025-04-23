import os
import json
import anthropic
from datasets import Dataset

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

def score_flexible_final_answer_claude(reasoning: str, final_answer: str) -> float:
    """
    Uses Claude (Anthropic) to judge the reasoning quality and final answer accuracy.
    The judge is lenient and focuses on logical plausibility, not formatting.
    """

    prompt = f"""
You are a financial reasoning tutor evaluating a student's explanation.

They were given a quantitative question and responded with the following explanation and final numeric answer.

Please be understanding — this is a model in training. Use this rubric:

- 1.0 = Excellent reasoning, clear logic, leads to correct or nearly correct final answer.
- 0.5 = Reasoning is partially correct or imprecise, but shows understanding.
- 0.0 = Reasoning is clearly flawed or answer is nonsensical.

Only reply with the numeric score: 1.0, 0.5, or 0.0.

---

Explanation:
{reasoning}

Final Answer:
{final_answer}

Score:"""

    try:
        response = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1,
            temperature=0,
            messages=[{"role": "user", "content": prompt}],
        )
        content = response.content[0].text.strip()
        return float(content)
    except Exception as e:
        print(f"[⚠️ Claude Eval Error] {e}")
        return 0.0


def evaluate_final_answer_accuracy_claude(dataset: Dataset, sample_size=100) -> float:
    """
    Evaluate a sample of dataset examples using Claude to judge the quality of their reasoning.
    """
    print("[🔍 Claude Evaluation] Scoring reasoning quality on subset...")
    subset = dataset.select(range(min(sample_size, len(dataset))))
    results = []
    for ex in subset:
        reasoning = ex.get("output", "")
        final = ex.get("Final Answer", "")
        score = score_flexible_final_answer_claude(reasoning, str(final))
        results.append(score)

    avg_score = sum(results) / len(results) if results else 0.0
    print(f"[✅ Claude Score]: {avg_score:.3f} over {len(results)} examples")
    return avg_score
