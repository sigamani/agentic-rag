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
