class MetricStabiliser:
    def __init__(self, window=3, threshold=0.002):
        self.history = {
            "loss": [],
            "accuracy": [],
            "claude_score": [],
        }
        self.window = window
        self.threshold = threshold

    def update(self, loss, accuracy, claude_score):
        self.history["loss"].append(loss)
        self.history["accuracy"].append(accuracy)
        self.history["claude_score"].append(claude_score)

    def _is_stable(self, values):
        if len(values) < self.window:
            return False
        recent = values[-self.window :]
        return max(recent) - min(recent) < self.threshold

    def should_stop(self):
        return all(
            [
                self._is_stable(self.history["loss"]),
                self._is_stable(self.history["accuracy"]),
                self._is_stable(self.history["claude_score"]),
            ]
        )



from langsmith.run_helpers import traceable
from langsmith import Client
import random

client = Client()

@traceable(name="log_langsmith_trace", project_name="pr-convfinqa-01", tags=["trace"])
def log_metrics_to_langsmith(example, model, phase_label, epoch_num):
    input_msg = example["input"]
    expected_answer = example.get("Final Answer", "")
    instruction = example["instruction"]

    prompt = f"""### Instruction:\n{instruction}\n\n### Input:\n{input_msg}"""

    response = model(prompt) if callable(model) else "[Model not callable]"

    print(f"\n[LangSmith Trace - {phase_label.upper()} | Epoch {epoch_num}]")
    print(f"Question: {input_msg}")
    print(f"Expected: {expected_answer}")
    print(f"Model Response: {response[:300]}...\n")

    return {"input": prompt, "output": response}
