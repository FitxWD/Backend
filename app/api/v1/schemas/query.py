from pydantic import BaseModel

class QueryRequest(BaseModel):
    query: str
    top_k: int = 3

class PlanRequest(BaseModel):
    user_answers: dict
    plan_type: str  # "diet" or "fitness"
    user_id: str