from langchain.tools import tool
import operator

@tool
def compute_qa_answer(sample: dict) -> dict:
    """Executes QA DSL (e.g., subtract, divide) and returns predicted vs gold answer."""
    try:
        prog = sample["qa"]["program"]
        parts = prog.split(",")
        arg1 = float(parts[0].split("(")[1])
        arg2 = float(parts[0].split(",")[1].strip(")"))
        intermediate = operator.sub(arg1, arg2)
        final = operator.truediv(intermediate, float(parts[1].split(",")[1].strip(")")))
        return {
            "question": sample["qa"]["question"],
            "gold_answer": sample["qa"]["answer"],
            "predicted_answer": f"{round(final * 100, 1)}%"
        }
    except Exception as e:
        return {"error": str(e)}
