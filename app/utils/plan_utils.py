from datetime import datetime
from typing import Dict, Any
from app.config import db

def get_diet_category(ml_prediction: int) -> str:
    """Convert ML prediction to diet category"""
    categories = {
        0: "Balanced",
        1: "Low_Carb",
        2: "Low_Sodium"
    }
    return categories.get(ml_prediction, "Balanced")

def find_nearest_calorie_bracket(calories: int) -> str:
    """Find the nearest calorie bracket in steps of 200"""
    base_calories = 1700
    max_calories = 3100
    step = 200
    
    # Find nearest bracket
    nearest = base_calories
    min_diff = abs(calories - base_calories)
    
    current = base_calories
    while current <= max_calories:
        diff = abs(calories - current)
        if diff < min_diff:
            min_diff = diff
            nearest = current
        current += step
    
    return str(nearest)

def store_user_diet_plan(user_id: str, plan_data: Dict[Any, Any]) -> Dict[str, Any]:
    """Store user diet plan in Firestore and return updated plan data"""
    try:
        ml_prediction = plan_data.get('ml_prediction')
        user_summary = plan_data.get('user_input_summary', {})
        calories = user_summary.get('calories', 2100)
        
        # Generate diet plan document name
        diet_category = get_diet_category(ml_prediction)
        calorie_bracket = find_nearest_calorie_bracket(int(calories))
        diet_doc_name = f"{diet_category}_{calorie_bracket}"
        
        # Get the referenced diet plan
        diet_plan_ref = db.collection("dietPlans").document(diet_doc_name)
        diet_plan_doc = diet_plan_ref.get()
        
        if not diet_plan_doc.exists:
            raise ValueError(f"Diet plan {diet_doc_name} not found")
        
        # Get user's plans collection
        user_plans_ref = db.collection("users").document(user_id)\
                         .collection("plans").document("diet")
        
        # Get current attempts
        user_plans_doc = user_plans_ref.get()
        current_attempts = 1
        
        if user_plans_doc.exists:
            plans_data = user_plans_doc.to_dict()
            current_attempts = len(plans_data.get("attempts", [])) + 1
        
        # Create new attempt data
        attempt_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "plan_id": diet_doc_name,
            "user_inputs": user_summary,
            "ml_prediction": ml_prediction
        }
        
        # Update user's plans document
        user_plans_ref.set({
            "attempts": {
                str(current_attempts): attempt_data
            }
        }, merge=True)
        
        # Update plan data with attempt info
        plan_data.update({
            "attempt_number": current_attempts,
            "assigned_plan_id": diet_doc_name
        })
        
        return plan_data
        
    except Exception as e:
        raise ValueError(f"Error storing diet plan: {str(e)}")
    
def get_fitness_category(ml_prediction: int) -> str:
    """Convert ML prediction to fitness category"""
    categories = {
        0: "gentle_start",
        1: "foundation_strength", 
        2: "play_and_perform",
        3: "the_endurance_engine",
        4: "the_express_burn"
    }
    return categories.get(ml_prediction, "gentle_start")

def store_user_fitness_plan(user_id: str, plan_data: Dict[Any, Any]) -> Dict[str, Any]:
    """Store user fitness plan in Firestore and return updated plan data"""
    try:
        ml_prediction = plan_data.get('ml_prediction')
        user_summary = plan_data.get('user_input_summary', {})
        
        # Generate fitness plan document name (just the category)
        fitness_category = get_fitness_category(ml_prediction)
        fitness_doc_name = fitness_category
        
        # FIXED: Use correct collection name
        fitness_plan_ref = db.collection("workoutPlans").document(fitness_doc_name)
        fitness_plan_doc = fitness_plan_ref.get()
        
        if not fitness_plan_doc.exists:
            # Fallback to gentle_start if plan not found
            fitness_doc_name = "gentle_start"
            fitness_plan_ref = db.collection("workoutPlans").document(fitness_doc_name)
            fitness_plan_doc = fitness_plan_ref.get()
            
            if not fitness_plan_doc.exists:
                raise ValueError(f"Fitness plan {fitness_doc_name} not found")
        
        # Get user's plans collection
        user_plans_ref = db.collection("users").document(user_id)\
                         .collection("plans").document("fitness")
        
        # Get current attempts
        user_plans_doc = user_plans_ref.get()
        current_attempts = 1
        
        if user_plans_doc.exists:
            plans_data = user_plans_doc.to_dict()
            current_attempts = len(plans_data.get("attempts", [])) + 1
        
        # Create new attempt data
        attempt_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "plan_id": fitness_doc_name,
            "user_inputs": user_summary,
            "ml_prediction": ml_prediction,
            "fitness_category": fitness_category
        }
        
        # Update user's plans document
        user_plans_ref.set({
            "attempts": {
                str(current_attempts): attempt_data
            }
        }, merge=True)
        
        # Update plan data with attempt info
        plan_data.update({
            "attempt_number": current_attempts,
            "assigned_plan_id": fitness_doc_name,
            "fitness_category": fitness_category
        })
        
        return plan_data
        
    except Exception as e:
        raise ValueError(f"Error storing fitness plan: {str(e)}")