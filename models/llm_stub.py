"""
Mock LLM for testing the financial RAG pipeline without requiring actual model downloads.
"""
from langchain_core.messages import AIMessage
import re

MODEL_NAME = "mock-financial-llm"

class MockLLM:
    """Mock LLM that generates realistic financial responses for testing."""
    
    def __init__(self, model=None):
        self.model = model or MODEL_NAME
    
    def invoke(self, input_text: str) -> str:
        """Generate mock response based on input patterns."""
        input_str = str(input_text).lower()
        
        # Mock financial reasoning responses
        if "percentage change" in input_str or "percent change" in input_str:
            return """<REASONING>
To calculate the percentage change, I'll use the formula:
percentage_change = ((new_value - old_value) / old_value) * 100

From the context provided:
- Old value: $200,000
- New value: $258,620

percentage_change = ((258,620 - 200,000) / 200,000) * 100
percentage_change = (58,620 / 200,000) * 100
percentage_change = 0.2931 * 100
percentage_change = 29.31%
</REASONING>

<ANSWER>29.31%</ANSWER>"""
        
        elif "search queries" in input_str or "queries:" in input_str:
            return """1. net cash operating activities 2008 2009
2. cash flow from operations percentage change
3. financial statement cash flow analysis"""
        
        elif "extract" in input_str and "answer" in input_str:
            # Extract answer from generation
            answer_match = re.search(r"<ANSWER>(.*?)</ANSWER>", input_text, re.DOTALL)
            if answer_match:
                return answer_match.group(1).strip()
            return "29.31%"
        
        elif "filter" in input_str or "relevant" in input_str:
            return """Net cash from operating activities was $200,000 in 2008.
Net cash from operating activities increased to $258,620 in 2009.

sources:
- financial-doc-2008
- financial-doc-2009"""
        
        else:
            # Default financial response
            return """Based on the financial data provided, the analysis shows a positive trend in the company's cash flow operations with an increase of approximately 29.31% year-over-year.

<ANSWER>29.31%</ANSWER>"""

# Create the mock LLM instance
llm = MockLLM()

def call_llm(prompt: str):
    """Mock LLM call for testing."""
    return llm.invoke(prompt)