from pydantic import BaseModel
from typing import Dict, Any, Optional

class QueryRequest(BaseModel):
    query: str
    top_k: int = 5

class PlanRequest(BaseModel):
    plan_type: str  # "diet" or "fitness"
    user_answers: Dict[str, Any]
    user_id: str