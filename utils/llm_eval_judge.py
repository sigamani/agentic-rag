from anthropic import Client as ClaudeClient
import os

client = ClaudeClient(api_key=os.environ["ANTHROPIC_API_KEY"])

def evaluate_final_answer_accuracy(dataset, sample_size):
    """
    Uses Claude to score reasoning and final answer quality.
    Always returns (average_score, sample_examples).
    """
    results = []
    examples = []
    subset = dataset.select(range(min(sample_size, len(dataset))))

    for ex in subset:
        reasoning = ex.get("output", "")
        expected_answer = ex.get("Final Answer", "")

        prompt = f"""\
    You are an expert tutor evaluating a student's financial reasoning.
    
    They gave the following explanation and final answer. Score how well it matches the correct answer.
    
    Be flexible with rounding and formatting. Use:
    
    - 1.0 = Strong logical reasoning, and correct or close final answer
    - 0.5 = Partial logic or unclear answer
    - 0.0 = Wrong or missing answer
    
    ---
    
    Reasoning:
    {reasoning}
    
    Expected Answer: {expected_answer}
    
    Score:"""

        try:
            response = client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=1,
                temperature=0,
                messages=[{"role": "user", "content": prompt}],
            )
            score = float(response.content[0].text.strip())
        except Exception as e:
            print(f"[Claude Eval Error] {e}")
            score = 0.0

        results.append(score)
        examples.append({
            "question": ex.get("input", ""),
            "model_reasoning": reasoning,
            "final_answer": expected_answer,
            "score": score,
        })

    avg_score = sum(results) / len(results) if results else 0.0
    print(f"[__ Claude Score]: {avg_score:.3f} over {len(results)} examples")
    return avg_score, examples
