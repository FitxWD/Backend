from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from app.deps.auth import verify_firebase_token
from app.config import db
from app.api.v1.schemas.user import ProfileUpdate, WorkoutPlan

router = APIRouter()

@router.get("/me")
def me(user=Depends(verify_firebase_token)) -> Dict[str, Any]:
    # user is decoded token; user["uid"] is the Firebase UID
    return {"uid": user["uid"], "email": user.get("email")}

@router.get("/profile")
def get_profile(user=Depends(verify_firebase_token)):
    uid = user["uid"]
    doc_ref = db.collection("users").document(uid).get()
    if doc_ref.exists:
        return doc_ref.to_dict()
    return {}

@router.post("/profile-health-update")
def upsert_profile(profile: ProfileUpdate, user=Depends(verify_firebase_token)):
    uid = user["uid"]
    profile_data = profile.dict(exclude_none=True)
    db.collection("users").document(uid).set(profile_data, merge=True)
    return {"ok": True}

@router.get("/workout-plan/{plan_id}", response_model=WorkoutPlan, response_model_exclude_none=True)
def get_workout_plan_details(plan_id: str):
    """
    Fetches a single workout plan by its document ID from Firestore.
    The refined 'WorkoutPlan' response_model ensures data integrity.
    'response_model_exclude_none=True' is a good practice to not send null fields in the JSON response.
    """
    try:
        plan_ref = db.collection("workoutPlans").document(plan_id)
        plan_document = plan_ref.get()

        if not plan_document.exists:
            raise HTTPException(status_code=404, detail="Workout plan not found")

        return plan_document.to_dict()

    except Exception as e:
        # This will catch validation errors from Pydantic if the data in Firestore
        # ever mismatches the schema in a new, unexpected way.
        raise HTTPException(status_code=500, detail=f"An error occurred processing the plan: {e}")