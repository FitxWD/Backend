from fastapi import APIRouter, Depends, HTTPException, Request, Query
from firebase_admin import auth, firestore
from typing import Dict, List, Any, Optional
from app.deps.auth import verify_firebase_token
from app.config import db
from app.api.v1.schemas.user import WorkoutPlan, DietPlan, DietPlanUpdate, FeedbackResponse, FeedbackStatus, UpdateStatusPayload, DashboardStats, FeedbackCountStats, RecentPlan, RecentFeedback, RecentUser, DailyGrowth, UserAdminView, UpdateAdminStatusPayload
from datetime import datetime, timedelta

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
    
@router.get("/feedbacks", response_model=List[FeedbackResponse])
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

@router.put("/feedback/{feedback_id}/status")
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
    
@router.get("/dashboard-stats", response_model=DashboardStats)
def get_dashboard_stats(user: Dict[str, Any] = Depends(verify_firebase_token)):
    """
    Aggregates and returns a rich set of statistics for the enhanced admin dashboard.
    """
    if not user.get("isAdmin"):
        raise HTTPException(status_code=403, detail="Forbidden: User is not an administrator")

    try:
        # --- Time calculations ---
        now = datetime.utcnow()
        today_start = datetime(now.year, now.month, now.day)
        seven_days_ago = today_start - timedelta(days=6) # Start of the 7-day window
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
        # Get Recent Users (most efficient query)
        recent_users_docs = db.collection("users").order_by("createdAt", direction=firestore.Query.DESCENDING).limit(5).stream()
        recent_users = []
        for doc in recent_users_docs:
            user_data = doc.to_dict()
            recent_users.append(
                RecentUser(
                    uid=doc.id,
                    email=user_data.get("email"),
                    createdAt=user_data.get("createdAt")
                )
            )

        # Get daily counts for the last 7 days
        daily_counts = { (today_start - timedelta(days=i)).strftime('%Y-%m-%d'): 0 for i in range(7) }
        
        # Query for all users created in the last 7 days
        users_last_7_days_query = db.collection("users").where("createdAt", ">=", seven_days_ago).stream()
        
        for doc in users_last_7_days_query:
            user_data = doc.to_dict()
            created_at = user_data.get("createdAt")
            
            # Ensure createdAt is a datetime object before formatting
            if isinstance(created_at, datetime):
                date_str = created_at.strftime('%Y-%m-%d')
                if date_str in daily_counts:
                    daily_counts[date_str] += 1
        
        user_growth_last_7_days = [DailyGrowth(date=d, count=c) for d, c in sorted(daily_counts.items())]
        
        # Get count of new users today (more efficient than filtering in Python)
        new_users_today_query = db.collection("users").where("createdAt", ">=", today_start).count()
        new_users_today = new_users_today_query.get()[0][0].value

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
            totalDietPlans=diet_plans_count,
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
    
@router.put("/workout-plan/{plan_id}")
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
    
@router.put("/diet-plan/{plan_id}")
def update_diet_plan(
    plan_id: str,
    plan_data: DietPlanUpdate,
    user: Dict[str, Any] = Depends(verify_firebase_token)
) -> Dict[str, str]:
    """
    Updates an entire diet plan document. Admin access is required.
    This endpoint automatically sets the 'lastEdited' timestamp.
    """
    # Admin Verification
    if not user.get("isAdmin"):
        raise HTTPException(status_code=403, detail="Forbidden: User is not an administrator")

    try:
        plan_ref = db.collection("dietPlans").document(plan_id)
        
        if not plan_ref.get().exists:
            raise HTTPException(status_code=404, detail="Diet plan not found")
        
        # Prepare the data for Firestore
        update_data = plan_data.dict(by_alias=True)
        
        # Set the lastEdited timestamp
        update_data["lastEdited"] = datetime.utcnow()
        
        # Use .update() to modify the document without deleting fields like diet_type
        plan_ref.update(update_data)
        
        return {"message": f"Diet plan '{plan_id}' updated successfully."}

    except Exception as e:
        print(f"Error updating diet plan: {e}")
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {e}")
    
@router.get("/users", response_model=List[UserAdminView])
def get_all_users():
    """
    Fetches a list of all Firebase users, including their admin status.
    Admin access is already verified by the router dependency.
    """
    try:
        all_users = []
        # auth.list_users() is the most efficient way to get all users
        for user_record in auth.list_users().iterate_all():
            claims = user_record.custom_claims or {}
            all_users.append(
                UserAdminView(
                    uid=user_record.uid,
                    email=user_record.email,
                    displayName=user_record.display_name,
                    isAdmin=claims.get("isAdmin", False),
                    # Convert ms timestamp to ISO string for the frontend
                    creationTime=datetime.utcfromtimestamp(user_record.user_metadata.creation_timestamp / 1000).isoformat() + "Z"
                )
            )
        # Sort by creation time, newest first
        all_users.sort(key=lambda x: x.creationTime, reverse=True)
        return all_users
    except Exception as e:
        print(f"Error fetching users: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch user list.")

@router.put("/users/{user_id}/status")
def update_user_admin_status(
    user_id: str,
    payload: UpdateAdminStatusPayload,
    # We need the current admin's token to prevent self-demotion
    admin_user: Dict[str, Any] = Depends(verify_firebase_token)
):
    """
    Updates a user's 'isAdmin' status in both Firestore and Firebase Auth claims.
    Prevents an admin from demoting themselves.
    """
    # CRUCIAL SAFETY CHECK: Prevent an admin from revoking their own admin rights
    if admin_user["uid"] == user_id and not payload.isAdmin:
        raise HTTPException(
            status_code=400,
            detail="Admins cannot revoke their own admin status."
        )

    try:
        # Step 1: Update the custom claim in Firebase Auth (for security)
        auth.set_custom_user_claims(user_id, {"isAdmin": payload.isAdmin})
        
        # Step 2: Update the 'source of truth' in the Firestore document (for consistency)
        user_doc_ref = db.collection("users").document(user_id)
        if user_doc_ref.get().exists:
            user_doc_ref.update({"isAdmin": payload.isAdmin})
        
        return {"message": "User admin status updated successfully."}
        
    except Exception as e:
        print(f"Error updating user status for {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update user status.")
    
@router.delete("/users/{user_id}")
def delete_user(
    user_id: str,
    # We still need the admin's token to verify they are an admin
    # and to prevent self-deletion
    admin_user: Dict[str, Any] = Depends(verify_firebase_token)
):
    """
    Deletes a user from Firebase Authentication.
    This is a permanent and irreversible action.
    Prevents an admin from deleting their own account.
    """
    # CRUCIAL SAFETY CHECK: Prevent an admin from deleting themselves
    if admin_user["uid"] == user_id:
        raise HTTPException(
            status_code=400,
            detail="Admins cannot delete their own account."
        )

    try:
        # Delete the user from Firebase Authentication
        auth.delete_user(user_id)
        
        # OPTIONAL: You could also delete their Firestore user document here
        user_doc_ref = db.collection("users").document(user_id)
        if user_doc_ref.get().exists:
            user_doc_ref.delete()
        
        return {"message": "User deleted successfully from authentication."}
        
    except auth.UserNotFoundError:
        raise HTTPException(status_code=404, detail="User not found in Firebase Authentication.")
    except Exception as e:
        print(f"Error deleting user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete user.")