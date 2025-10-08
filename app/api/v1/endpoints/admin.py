from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Dict, List, Any
from app.deps.auth import verify_firebase_token
from app.config import db
from app.api.v1.schemas.user import WorkoutPlan, DietPlan

router = APIRouter()

# Helper function for admin verification
def verify_admin_token(request: Request):
    return verify_firebase_token(request, require_admin=True)

@router.get("/workout-plan/{plan_id}", response_model=WorkoutPlan, response_model_exclude_none=True)
def get_workout_plan_details(
    plan_id: str,
    user=Depends(verify_admin_token)
):
    """
    Admin route to fetch workout plan details.
    Requires admin privileges to access.
    """
    try:
        plan_ref = db.collection("workoutPlans").document(plan_id)
        plan_document = plan_ref.get()

        if not plan_document.exists:
            raise HTTPException(status_code=404, detail="Workout plan not found")

        return plan_document.to_dict()

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching workout plan: {str(e)}"
        )

@router.get("/diet-plan/{plan_id}", response_model=DietPlan, response_model_exclude_none=True)
def get_diet_plan_details(
    plan_id: str,
    user=Depends(verify_admin_token)
):
    """
    Admin route to fetch diet plan details.
    Requires admin privileges to access.
    """
    try:
        plan_ref = db.collection("dietPlans").document(plan_id)
        plan_document = plan_ref.get()

        if not plan_document.exists:
            raise HTTPException(status_code=404, detail="Diet plan not found")

        return plan_document.to_dict()

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching diet plan: {str(e)}"
        )

@router.get("/all-workout-plans", response_model=List[WorkoutPlan])
def get_all_workout_plans(
    user=Depends(verify_admin_token)
):
    """
    Admin route to fetch all workout plans.
    """
    try:
        plans = db.collection("workoutPlans").stream()
        return [
            {
                "id": doc.id,
                **doc.to_dict()
            } 
            for doc in plans
        ]

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching workout plans: {str(e)}"
        )

@router.get("/all-diet-plans", response_model=List[DietPlan])
def get_all_diet_plans(
    user=Depends(verify_admin_token)
):
    """
    Admin route to fetch all diet plans.
    """
    try:
        plans = db.collection("dietPlans").stream()
        return [
            {
                "id": doc.id,
                **doc.to_dict()
            } 
            for doc in plans
        ]

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching diet plans: {str(e)}"
        )