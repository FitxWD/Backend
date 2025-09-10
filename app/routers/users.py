from fastapi import APIRouter
from app.config import db

router = APIRouter()

@router.post("/users/{user_id}")
def create_user(user_id: str, name: str, email: str, preferences: dict = {}):
    user_ref = db.collection("users").document(user_id)
    user_ref.set({
        "name": name,
        "email": email,
        "preferences": preferences,
        "customizedWorkoutPlans": [],
        "customizedDietPlans": []
    })
    return {"message": "User created", "id": user_id}
