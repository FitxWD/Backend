from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, List, Any, Optional
from app.deps.auth import verify_firebase_token
from app.config import db
from app.api.v1.schemas.user import ProfileUpdate, WorkoutPlan, DietPlan, PlanAcceptanceRequest, FeedbackPayload, FeedbackResponse, FeedbackStatus, UpdateStatusPayload, DashboardStats, FeedbackCountStats, RecentFeedback, RecentUser, DailyGrowth, RecentPlan
from datetime import datetime, timedelta
from firebase_admin import auth, firestore


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

@router.get("/admin/feedbacks", response_model=List[FeedbackResponse])
def get_all_feedbacks(
    status: Optional[FeedbackStatus] = Query(None, description="Filter feedbacks by status"),
    user: Dict[str, Any] = Depends(verify_firebase_token)
) -> List[FeedbackResponse]:
    """
    Fetches user feedbacks. Admin access is verified at the start of the function.
    """
    if not user.get("isAdmin"):
        raise HTTPException(status_code=403, detail="Forbidden: User is not an administrator")
    
    try:
        # --- FIX 1: Use the correct collection name 'feedbacks' (plural) ---
        query = db.collection("feedbacks") 
        
        if status:
            query = query.where("status", "==", status)
        
        docs = query.order_by("createdAt", direction=firestore.Query.DESCENDING).stream()
        
        response_data = []
        for doc in docs:
            feedback = doc.to_dict()
            user_info = {"uid": feedback.get("userId")}
            
            try:
                user_record = auth.get_user(feedback.get("userId"))
                user_info["email"] = user_record.email
                user_info["displayName"] = user_record.display_name
            except auth.UserNotFoundError:
                user_info["email"] = "Deleted User"

            # --- FIX 2: Explicitly map fields instead of using **feedback ---
            # This avoids the error by not passing the unexpected 'userId' field.
            response_data.append(
                FeedbackResponse(
                    id=doc.id,
                    user=user_info,
                    planId=feedback.get("planId"),
                    rating=feedback.get("rating"),
                    text=feedback.get("text"),
                    createdAt=feedback.get("createdAt"),
                    status=feedback.get("status")
                )
            )
            
        return response_data
            
    except Exception as e:
        # It's helpful to print the error for debugging
        print(f"Error in get_all_feedbacks: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch feedbacks: {e}")

@router.put("/admin/feedback/{feedback_id}/status")
def update_feedback_status(
    feedback_id: str,
    payload: UpdateStatusPayload,
    user: Dict[str, Any] = Depends(verify_firebase_token)
) -> Dict[str, str]:
    """
    Updates a feedback's status. Admin access is verified at the start of the function.
    """
    if not user.get("isAdmin"):
        raise HTTPException(status_code=403, detail="Forbidden: User is not an administrator")

    try:
        # --- FIX 1 (Applied here too): Use the correct collection name 'feedbacks' ---
        feedback_doc_ref = db.collection("feedbacks").document(feedback_id)
        
        if not feedback_doc_ref.get().exists:
            raise HTTPException(status_code=404, detail="Feedback not found")
        
        feedback_doc_ref.update({"status": payload.status})
        
        return {"message": "Feedback status updated successfully"}
    
    except Exception as e:
        print(f"Error in update_feedback_status: {e}")
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {e}")
    
@router.get("/admin/dashboard-stats", response_model=DashboardStats)
def get_dashboard_stats(user: Dict[str, Any] = Depends(verify_firebase_token)):
    """
    Aggregates and returns a rich set of statistics for the enhanced admin dashboard.
    """
    if not user.get("isAdmin"):
        raise HTTPException(status_code=403, detail="Forbidden: User is not an administrator")

    try:
        # --- Time calculations ---
        now = datetime.utcnow()
        yesterday = now - timedelta(days=1)

        # --- 1. Aggregate Counts (as before) ---
        users_count = db.collection("users").count().get()[0][0].value
        workout_plans_count = db.collection("workoutPlans").count().get()[0][0].value
        diet_plans_count = db.collection("dietPlans").count().get()[0][0].value
        new_feedbacks_count = db.collection("feedbacks").where("status", "==", "new").count().get()[0][0].value
        reviewed_feedbacks_count = db.collection("feedbacks").where("status", "==", "reviewed").count().get()[0][0].value

        # --- 2. NEW: Count recently edited plans ---
        # Note: This requires a composite index on 'lastEdited'. Firestore will provide a link to create it if needed.
        workout_plans_edited_query = db.collection("workoutPlans").where("lastEdited", ">=", yesterday).count()
        diet_plans_edited_query = db.collection("dietPlans").where("lastEdited", ">=", yesterday).count()
        
        workout_plans_edited_today = workout_plans_edited_query.get()[0][0].value
        diet_plans_edited_today = diet_plans_edited_query.get()[0][0].value

        # --- 2. Get Recent Activities ---
        # Recent Feedbacks (last 5 new)
        recent_feedbacks_docs = db.collection("feedbacks").where("status", "==", "new").order_by("createdAt", direction=firestore.Query.DESCENDING).limit(5).stream()
        recent_feedbacks = []
        for doc in recent_feedbacks_docs:
            fb = doc.to_dict()
            try:
                user_record = auth.get_user(fb.get("userId"))
                email = user_record.email
            except auth.UserNotFoundError:
                email = "Deleted User"
            recent_feedbacks.append(RecentFeedback(id=doc.id, text=fb.get("text"), rating=fb.get("rating"), userEmail=email))
            
        # --- 3. Get User Growth Data ---
        now = datetime.utcnow()
        today_start = datetime(now.year, now.month, now.day)
        
        # Recent Users (last 5 sign-ups) & Daily Growth for 7 days
        recent_users = []
        daily_counts = { (today_start - timedelta(days=i)).strftime('%Y-%m-%d'): 0 for i in range(7) }
        new_users_today = 0
        
        # auth.list_users() is efficient for getting all users
        for user_record in auth.list_users().iterate_all():
            # Timestamps from auth are in milliseconds
            created_at_dt = datetime.utcfromtimestamp(user_record.user_metadata.creation_timestamp / 1000)
            
            # Add to recent users list
            if len(recent_users) < 5:
                recent_users.append(RecentUser(uid=user_record.uid, email=user_record.email, createdAt=created_at_dt))
            
            # Tally daily counts
            if created_at_dt >= today_start:
                new_users_today += 1
            
            date_str = created_at_dt.strftime('%Y-%m-%d')
            if date_str in daily_counts:
                daily_counts[date_str] += 1

        # Sort recent_users by creation time
        recent_users.sort(key=lambda x: x.createdAt, reverse=True)
        user_growth_last_7_days = [DailyGrowth(date=d, count=c) for d, c in sorted(daily_counts.items())]

        # --- 4. Get Plan Generation Count (Proxy) ---
        # This is a proxy. A more accurate way would be to log generation events.
        # Here, we count all plan attempts in the last 24 hours.
        plans_generated_today = 0
        all_users = db.collection("users").stream()
        yesterday = now - timedelta(days=1)

        for u_doc in all_users:
            for plan_type in ["diet", "fitness"]:
                attempts = u_doc.to_dict().get("plans", {}).get(plan_type, {}).get("attempts", {})
                for attempt in attempts.values():
                    # Timestamps might be strings, so they need parsing
                    attempt_ts_str = attempt.get("timestamp")
                    if attempt_ts_str:
                        attempt_dt = datetime.fromisoformat(attempt_ts_str.replace("Z", "+00:00"))
                        if attempt_dt > yesterday:
                            plans_generated_today += 1
        
        diet_plans_query = db.collection("dietPlans").order_by("lastEdited", direction=firestore.Query.DESCENDING).limit(5).stream()
        workout_plans_query = db.collection("workoutPlans").order_by("lastEdited", direction=firestore.Query.DESCENDING).limit(5).stream()

        all_recent_plans = []
        for doc in diet_plans_query:
            plan = doc.to_dict()
            if 'lastEdited' in plan: # Ensure the field exists before adding
                all_recent_plans.append(RecentPlan(id=doc.id, name=plan.get("name", doc.id), type="diet", lastEdited=plan.get("lastEdited")))

        for doc in workout_plans_query:
            plan = doc.to_dict()
            if 'lastEdited' in plan: # Ensure the field exists before adding
                all_recent_plans.append(RecentPlan(id=doc.id, name=plan.get("name", doc.id), type="workout", lastEdited=plan.get("lastEdited")))

        all_recent_plans.sort(key=lambda x: x.lastEdited, reverse=True)
        recently_edited_plans = all_recent_plans[:5]

        # --- 5. Assemble Final Response ---
        return DashboardStats(
            totalUsers=users_count,
            newUsersToday=new_users_today,
            feedbackCounts=FeedbackCountStats(new=new_feedbacks_count, reviewed=reviewed_feedbacks_count, total=new_feedbacks_count + reviewed_feedbacks_count),
            totalWorkoutPlans=workout_plans_count,
            totalDietPlans=diet_plans_count,#
            workoutPlansEditedToday=workout_plans_edited_today,
            dietPlansEditedToday=diet_plans_edited_today,
            recentlyEditedPlans=recently_edited_plans,    
            recentFeedbacks=recent_feedbacks,
            recentUsers=recent_users,
            userGrowthLast7Days=user_growth_last_7_days
        )

    except Exception as e:
        print(f"Error fetching enhanced dashboard stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to aggregate dashboard statistics.")
    
@router.put("/admin/workout-plan/{plan_id}")
def update_workout_plan(
    plan_id: str,
    plan_data: WorkoutPlan,
    user: Dict[str, Any] = Depends(verify_firebase_token)
) -> Dict[str, str]:
    """
    Updates a workout plan document. Admin access is required.
    This endpoint automatically sets the 'lastEdited' timestamp.
    """
    if not user.get("isAdmin"):
        raise HTTPException(status_code=403, detail="Forbidden: User is not an administrator")

    try:
        plan_ref = db.collection("workoutPlans").document(plan_id)
        
        if not plan_ref.get().exists:
            raise HTTPException(status_code=404, detail="Workout plan not found")
        
        # Prepare the data, still excluding name and level to prevent them from being changed
        update_data = plan_data.dict(by_alias=True, exclude={"name", "level"})
        
        # Set the lastEdited timestamp
        update_data["lastEdited"] = datetime.utcnow()
        
        # --- THE FIX: Use .update() to modify existing fields without deleting others ---
        plan_ref.update(update_data)
        
        return {"message": f"Workout plan '{plan_id}' updated successfully."}

    except Exception as e:
        print(f"Error updating workout plan: {e}")
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {e}")