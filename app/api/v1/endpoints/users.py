from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from app.deps.auth import verify_firebase_token
from app.config import db
from app.api.v1.schemas.user import ProfileUpdate, WorkoutPlan, DietPlan, PlanAcceptanceRequest
from datetime import datetime


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

@router.get("/user-health-data/{user_id}")
def get_user_health_data(user_id: str, user=Depends(verify_firebase_token)):
    # Verify if the requesting user has permission to access this data
    if user["uid"] != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this user's data")
    
    # Fetch user health data from Firestore
    doc_ref = db.collection("users").document(user_id).get()
    if doc_ref.exists:
        user_data = doc_ref.to_dict()
        health_data = user_data.get("healthData", {})
        return health_data
    
    raise HTTPException(status_code=404, detail="User health data not found")

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
    
@router.get("/diet-plan/{plan_id}", response_model=DietPlan, response_model_exclude_none=True)
def get_diet_plan_details(plan_id: str):
    """
    Fetches a single diet plan by its document ID from the 'dietPlans' collection.
    Example plan_id: 'Balanced_1700'
    """
    try:
        plan_ref = db.collection("dietPlans").document(plan_id)
        plan_document = plan_ref.get()

        if not plan_document.exists:
            raise HTTPException(status_code=404, detail="Diet plan not found")

        return plan_document.to_dict()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred processing the plan: {e}")

@router.post("/accept-plan")
def accept_plan(request: PlanAcceptanceRequest, user=Depends(verify_firebase_token)):
    """
    Handle plan acceptance and update user's current plan
    """
    try:
        # Verify user authorization
        if user["uid"] != request.user_id:
            raise HTTPException(
                status_code=403, 
                detail="Not authorized to update this user's plan"
            )
        
        # Verify plan exists
        plan_ref = db.collection(f"{request.plan_type}Plans").document(request.plan_id)
        if not plan_ref.get().exists:
            raise HTTPException(
                status_code=404, 
                detail=f"{request.plan_type} plan not found"
            )
        
        # Get user document and current plan
        user_ref = db.collection("users").document(request.user_id)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            raise HTTPException(status_code=404, detail="User not found")
            
        user_data = user_doc.to_dict()
        current_plan_field = f"current{request.plan_type.capitalize()}Plan"
        current_plan = user_data.get(current_plan_field)

        if request.accepted:
            # Only update if accepting a new plan
            update_data = {
                current_plan_field: {
                    "plan_id": request.plan_id,
                    "accepted_at": datetime.utcnow(),
                    "status": "active"
                }
            }
            # Update user document
            user_ref.update(update_data)
            message = "Plan accepted successfully"
        else:
            # If rejecting and there's a current plan, keep it
            if current_plan:
                message = "Plan rejected, keeping current plan"
            else:
                message = "Plan rejected"
            # No update needed when rejecting - keep existing plan
        
        return {
            "status": "success",
            "message": message,
            "plan_id": current_plan["plan_id"] if not request.accepted and current_plan else request.plan_id,
            "current_plan": current_plan
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error updating plan acceptance: {str(e)}"
        )