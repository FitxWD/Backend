from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, List, Any, Optional
from app.deps.auth import verify_firebase_token
from app.config import db
from app.api.v1.schemas.user import ProfileUpdate, WorkoutPlan, DietPlan, PlanAcceptanceRequest, FeedbackPayload, FeedbackResponse, FeedbackStatus, UpdateStatusPayload, DashboardStats, FeedbackCountStats, RecentFeedback, RecentUser, DailyGrowth, RecentPlan, DietPlanUpdate
from datetime import datetime
from firebase_admin import auth


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

@router.get("/plan-history")
def get_plan_history(user=Depends(verify_firebase_token)) -> Dict[str, Any]:
    """
    Get user's complete plan history for both diet and fitness plans.
    Returns attempts sorted by timestamp in descending order.
    """
    try:
        uid = user["uid"]
        
        # Get diet plans history
        diet_plans_ref = db.collection("users").document(uid)\
                          .collection("plans").document("diet")
        diet_doc = diet_plans_ref.get()
        
        # Get fitness plans history
        fitness_plans_ref = db.collection("users").document(uid)\
                             .collection("plans").document("fitness")
        fitness_doc = fitness_plans_ref.get()
        
        # Initialize response structure
        plan_history = {
            "diet_plans": [],
            "fitness_plans": [],
            "current_plans": {}
        }
        
        # Process diet plans
        if diet_doc.exists:
            diet_data = diet_doc.to_dict()
            attempts = diet_data.get("attempts", {})
            diet_plans = [
                {
                    "attempt_number": int(attempt_num),
                    **attempt_data
                }
                for attempt_num, attempt_data in attempts.items()
            ]
            # Sort by timestamp descending
            diet_plans.sort(key=lambda x: x["timestamp"], reverse=True)
            plan_history["diet_plans"] = diet_plans
            
        # Process fitness plans
        if fitness_doc.exists:
            fitness_data = fitness_doc.to_dict()
            attempts = fitness_data.get("attempts", {})
            fitness_plans = [
                {
                    "attempt_number": int(attempt_num),
                    **attempt_data
                }
                for attempt_num, attempt_data in attempts.items()
            ]
            # Sort by timestamp descending
            fitness_plans.sort(key=lambda x: x["timestamp"], reverse=True)
            plan_history["fitness_plans"] = fitness_plans
            
        # Get current active plans
        user_doc = db.collection("users").document(uid).get()
        if user_doc.exists:
            user_data = user_doc.to_dict()
            plan_history["current_plans"] = {
                "diet": user_data.get("currentDietPlan"),
                "fitness": user_data.get("currentWorkoutPlan")
            }
        
        return plan_history
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching plan history: {str(e)}"
        )

@router.get("/current-plans")
def get_current_plans(user=Depends(verify_firebase_token)) -> Dict[str, Any]:
    """
    Get user's current active diet and fitness plans with detailed information.
    Returns comprehensive plan details for frontend display.
    """
    try:
        uid = user["uid"]
        user_doc = db.collection("users").document(uid).get()
        
        if not user_doc.exists:
            return {
                "diet": None,
                "fitness": None,
                "has_active_plans": False,
                "last_updated": None
            }
            
        user_data = user_doc.to_dict()
        current_diet = user_data.get("currentDietPlan")
        current_workout = user_data.get("currentWorkoutPlan")
        
        # Fetch detailed diet plan information
        diet_details = None
        if current_diet and current_diet.get("plan_id"):
            diet_doc = db.collection("dietPlans").document(current_diet["plan_id"]).get()
            if diet_doc.exists:
                plan_data = diet_doc.to_dict()
                diet_details = {
                    **current_diet,

                    "calorie_range": plan_data.get("calorie_range"),
                    "macro_targets": {
                        "carbs_g": plan_data.get("macro_targets", {}).get("carbs_g"),
                        "fat_g": plan_data.get("macro_targets", {}).get("fat_g"),
                        "protein_g": plan_data.get("macro_targets", {}).get("protein_g")
                    },
                    "notes": plan_data.get("notes")
                }
        
        # Fetch detailed workout plan information
        workout_details = None
        if current_workout and current_workout.get("plan_id"):
            workout_doc = db.collection("workoutPlans").document(current_workout["plan_id"]).get()
            if workout_doc.exists:
                plan_data = workout_doc.to_dict()
                workout_details = {
                    **current_workout,
                    "name": plan_data.get("name"),
                    "level": plan_data.get("level"),
                    "description": plan_data.get("description"),
                    "durationMinutes": plan_data.get("durationMinutes", 60),
                }
        
        # Calculate last_updated safely
        diet_updated = current_diet.get("accepted_at") if current_diet else None
        workout_updated = current_workout.get("accepted_at") if current_workout else None
        
        last_updated = None
        if diet_updated and workout_updated:
            last_updated = max(diet_updated, workout_updated)
        elif diet_updated:
            last_updated = diet_updated
        elif workout_updated:
            last_updated = workout_updated
        
        return {
            "diet": diet_details,
            "fitness": workout_details,
            "has_active_plans": bool(diet_details or workout_details),
            "last_updated": last_updated
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching current plans: {str(e)}"
        )

@router.post("/set-custom-claim")
def set_custom_claim(user=Depends(verify_firebase_token)) -> Dict[str, Any]:
    """
    Check user's custom status from Firestore and set Firebase claim accordingly.
    Called after login to determine user role and redirect path.
    """
    try:
        uid = user["uid"]
        
        # Check admin status from Firestore
        user_doc = db.collection("users").document(uid).get()
        
        if not user_doc.exists:
            raise HTTPException(
                status_code=404,
                detail="User document not found"
            )
            
        user_data = user_doc.to_dict()
        is_admin = user_data.get("isAdmin", False)
        
        # Set or update custom claims based on Firestore data
        auth.set_custom_user_claims(uid, {
            "isAdmin": is_admin,
            "modifiedAt": datetime.utcnow().isoformat()
        })

        return {
            "status": "success",
            "isAdmin": is_admin,  # Return flag for frontend routing
            "uid": uid,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error checking admin status: {str(e)}"
        )

@router.post("/feedback")
def submit_feedback(
    payload: FeedbackPayload, 
    user: Dict[str, Any] = Depends(verify_firebase_token)
) -> Dict[str, str]:
    """
    Receives and stores user feedback for a specific plan.
    """
    try:
        uid = user["uid"]
        
        # The data is already validated by the FeedbackPayload model
        feedback_data = {
            "userId": uid,
            "planId": payload.planId,
            "rating": payload.rating,
            "text": payload.text,
            "createdAt": datetime.utcnow().isoformat() + "Z", # Use UTC time,
            "status": "new" 
        }
        
        # Get the feedback collection and add a new document
        feedback_collection = db.collection("feedbacks")
        feedback_collection.add(feedback_data)
        
        return {"message": "Feedback submitted successfully"}
        
    except Exception as e:
        print(f"Feedback submission error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"An internal error occurred while saving feedback: {str(e)}"
        )

