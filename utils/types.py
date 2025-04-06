from pydantic import BaseModel, Field
from typing import Optional


class EvaluationResult(BaseModel):
    score: float = Field(..., alias="Score")
    reasoning: Optional[str] = Field(None, alias="Explanation")
