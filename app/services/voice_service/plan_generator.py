import pickle
import pandas as pd
import numpy as np
import os
from typing import Dict, Any
import joblib  # Alternative to pickle

# Load the saved diet model
def load_diet_model():
    """Load the saved diet prediction model"""
    model_paths = [
        "models/diet_model.pkl",
        "models/diet_model.joblib", 
        "diet_model.pkl",
        "diet_model.joblib"
    ]
    
    for model_path in model_paths:
        try:
            if os.path.exists(model_path):
                print(f"Trying to load model from: {model_path}")
                
                # Try different loading methods
                if model_path.endswith('.joblib'):
                    model = joblib.load(model_path)
                else:
                    # Try different pickle protocols
                    try:
                        with open(model_path, 'rb') as f:
                            model = pickle.load(f)
                    except Exception as e1:
                        print(f"Standard pickle failed: {e1}")
                        try:
                            # Try with protocol 2 (older Python compatibility)
                            with open(model_path, 'rb') as f:
                                model = pickle.load(f, encoding='latin1')
                        except Exception as e2:
                            print(f"Latin1 encoding failed: {e2}")
                            try:
                                # Try with joblib as fallback
                                model = joblib.load(model_path)
                            except Exception as e3:
                                print(f"Joblib fallback failed: {e3}")
                                continue
                
                print(f"Diet model loaded successfully from: {model_path}")
                print(f"Model type: {type(model)}")
                return model
                
        except Exception as e:
            print(f"Error loading model from {model_path}: {e}")
            continue
    
    print("Could not load diet model from any path. Using fallback plan generation.")
    return None

# Global model instance
_diet_model = None

def get_diet_model():
    global _diet_model
    if _diet_model is None:
        _diet_model = load_diet_model()
    return _diet_model

def transform_diet_answers_to_model_input(user_answers: dict) -> dict:
    """Transform user answers to match the diet model's expected input format"""
    
    # Initialize the feature dictionary with all columns set to 0
    encoded_columns = [
        'Age', 'Weight_kg', 'Height_cm', 'BMI', 'Severity', 'Physical_Activity_Level',
        'Cholesterol_mg/dL', 'Blood_Pressure_mmHg', 'Glucose_mg/dL',
        'Weekly_Exercise_Hours', 'Calculated_Calorie_Intake',
        'Gender_Female', 'Gender_Male',
        'Disease_Type_Diabetes', 'Disease_Type_Hypertension', 'Disease_Type_Obesity',
        'Dietary_Restrictions_Low_Sodium', 'Dietary_Restrictions_Low_Sugar',
        'Allergies_Gluten', 'Allergies_Peanuts',
        'Preferred_Cuisine_Chinese', 'Preferred_Cuisine_Indian',
        'Preferred_Cuisine_Italian', 'Preferred_Cuisine_Mexican'
    ]
    
    # Initialize all features to 0
    features = {col: 0 for col in encoded_columns}
    
    print(f"Debug - Input answers: {user_answers}")
    
    # Extract and transform answers based on your finalized questions
    # FIXED MAPPING: Q0, Q1, Q2... instead of Q1, Q2, Q3...
    
    # Q0: Age - "First, may I know your age?"
    age = extract_number(user_answers.get("Q0", "25"))
    features['Age'] = age
    print(f"Debug - Age: {age}")
    
    # Q1: Gender - "What is your gender? (Male, Female, or Other)"
    gender = user_answers.get("Q1", "").lower()
    if "female" in gender:
        features['Gender_Female'] = 1
        features['Gender_Male'] = 0
    elif "male" in gender:
        features['Gender_Male'] = 1
        features['Gender_Female'] = 0
    else:  # Other or unknown, default to male
        features['Gender_Male'] = 1
        features['Gender_Female'] = 0
    print(f"Debug - Gender: {gender}, Female: {features['Gender_Female']}, Male: {features['Gender_Male']}")
    
    # Q2: Height - "Could you tell me your height in centimeters?"
    height = extract_number(user_answers.get("Q2", "170"))
    features['Height_cm'] = height
    print(f"Debug - Height: {height}")
    
    # Q3: Weight - "And your weight in kilograms?"
    weight = extract_number(user_answers.get("Q3", "70"))
    features['Weight_kg'] = weight
    print(f"Debug - Weight: {weight}")
    
    # Calculate BMI
    height_m = height / 100
    bmi = weight / (height_m ** 2) if height_m > 0 else 25
    features['BMI'] = bmi
    print(f"Debug - BMI: {bmi}")
    
    # Q4: Health conditions - "Do you have any health conditions such as hypertension, diabetes, or obesity?"
    conditions = user_answers.get("Q4", "").lower()
    if "diabetes" in conditions:
        features['Disease_Type_Diabetes'] = 1
    if "hypertension" in conditions or "blood pressure" in conditions or "bp" in conditions:
        features['Disease_Type_Hypertension'] = 1
    if "obesity" in conditions or "obese" in conditions:
        features['Disease_Type_Obesity'] = 1
    print(f"Debug - Conditions: {conditions}")
    
    # Q5: Severity - "How would you describe the severity of your condition? (Mild, Moderate, or Severe)"
    severity = user_answers.get("Q5", "").lower()
    if "severe" in severity:
        features['Severity'] = 2
    elif "moderate" in severity:
        features['Severity'] = 1
    elif "mild" in severity:
        features['Severity'] = 0
    else:
        features['Severity'] = 0  # No condition or not specified
    print(f"Debug - Severity: {severity}, mapped to: {features['Severity']}")
    
    # Q6: Activity level - "How active are you in your daily life? (Sedentary, Moderate, or Active)"
    activity = user_answers.get("Q6", "").lower()
    if "sedentary" in activity:
        features['Physical_Activity_Level'] = 0
    elif "moderate" in activity:
        features['Physical_Activity_Level'] = 1
    elif "active" in activity:
        features['Physical_Activity_Level'] = 2
    else:
        features['Physical_Activity_Level'] = 1  # Default to moderate
    print(f"Debug - Activity: {activity}, mapped to: {features['Physical_Activity_Level']}")
    
    # Q7: Cholesterol - "What is your cholesterol level in mg/dL?"
    cholesterol = extract_number(user_answers.get("Q7", "200"))
    features['Cholesterol_mg/dL'] = cholesterol if cholesterol > 0 else 200  # Default normal value
    print(f"Debug - Cholesterol: {cholesterol}")
    
    # Q8: Blood pressure - "What is your blood pressure in mmHg?"
    bp = extract_number(user_answers.get("Q8", "120"))
    features['Blood_Pressure_mmHg'] = bp if bp > 0 else 120  # Default normal systolic
    print(f"Debug - Blood Pressure: {bp}")
    
    # Q9: Glucose - "What is your glucose level in mg/dL?"
    glucose = extract_number(user_answers.get("Q9", "100"))
    features['Glucose_mg/dL'] = glucose if glucose > 0 else 100  # Default normal fasting glucose
    print(f"Debug - Glucose: {glucose}")
    
    # Q10: Dietary restrictions - "Do you have any dietary restrictions, such as low sodium or low sugar?"
    restrictions = user_answers.get("Q10", "").lower()
    if "low sodium" in restrictions or "sodium" in restrictions:
        features['Dietary_Restrictions_Low_Sodium'] = 1
    if "low sugar" in restrictions or "sugar" in restrictions:
        features['Dietary_Restrictions_Low_Sugar'] = 1
    print(f"Debug - Restrictions: {restrictions}")
    
    # Q11: Allergies - "Are you allergic to any foods, like gluten or peanuts?"
    allergies = user_answers.get("Q11", "").lower()
    if "gluten" in allergies:
        features['Allergies_Gluten'] = 1
    if "peanut" in allergies or "nut" in allergies:
        features['Allergies_Peanuts'] = 1
    print(f"Debug - Allergies: {allergies}")
    
    # Q12: Cuisine preference - "What type of cuisine do you prefer? (Mexican, Indian, Chinese, or Italian)"
    cuisine = user_answers.get("Q12", "").lower()
    if "chinese" in cuisine:
        features['Preferred_Cuisine_Chinese'] = 1
    elif "indian" in cuisine:
        features['Preferred_Cuisine_Indian'] = 1
    elif "italian" in cuisine:
        features['Preferred_Cuisine_Italian'] = 1
    elif "mexican" in cuisine:
        features['Preferred_Cuisine_Mexican'] = 1
    print(f"Debug - Cuisine: {cuisine}, Chinese: {features['Preferred_Cuisine_Chinese']}")
    
    # Q13: Exercise hours - "How many hours do you exercise per week?"
    exercise_hours = extract_number(user_answers.get("Q13", "3"))
    features['Weekly_Exercise_Hours'] = exercise_hours
    print(f"Debug - Exercise hours: {exercise_hours}")
    
    # Calculate calorie intake using Mifflin-St Jeor equation
    if features['Gender_Male']:
        bmr = 10 * weight + 6.25 * height - 5 * age + 5  # Male formula
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161  # Female formula
    
    # Activity multiplier based on activity level (adjusted mapping)
    activity_multiplier = {0: 1.2, 1: 1.375, 2: 1.55}.get(features['Physical_Activity_Level'], 1.375)
    calculated_calories = bmr * activity_multiplier
    
    features['Calculated_Calorie_Intake'] = int(calculated_calories)
    print(f"Debug - BMR: {bmr}, Activity Multiplier: {activity_multiplier}, Calculated Calories: {calculated_calories}")
    
    print(f"Final transformed features: {features}")
    return features

def extract_number(text: str) -> float:
    """Extract numeric value from text"""
    import re
    # Handle common responses
    text = str(text).lower()
    
    # Handle "don't know", "unknown", etc.
    dont_know_phrases = ["don't know", "unknown", "not sure", "no idea", "unsure", "none", "joked from game"]
    if any(phrase in text for phrase in dont_know_phrases):
        return 0
    
    # Extract numbers
    numbers = re.findall(r'\d+\.?\d*', text)
    return float(numbers[0]) if numbers else 0

def generate_diet_plan(user_answers: dict) -> dict:
    """Generate diet plan using ML model prediction"""
    try:
        print(f"Generating diet plan with answers: {user_answers}")
        
        # Transform answers to model input format
        model_input = transform_diet_answers_to_model_input(user_answers)
        
        # Validate the transformed input
        if model_input['Age'] == 0 or model_input['Weight_kg'] == 0 or model_input['Height_cm'] == 0:
            print("Warning: Missing critical data (age, weight, or height). Using enhanced fallback plan.")
            return generate_enhanced_fallback_diet_plan(user_answers, model_input)
        
        # Load the ML model
        model = get_diet_model()
        if model is None:
            print("ML model not available, using enhanced fallback plan")
            return generate_enhanced_fallback_diet_plan(user_answers, model_input)
        
        # Prepare input for prediction
        encoded_columns = [
            'Age', 'Weight_kg', 'Height_cm', 'BMI', 'Severity', 'Physical_Activity_Level',
            'Cholesterol_mg/dL', 'Blood_Pressure_mmHg', 'Glucose_mg/dL',
            'Weekly_Exercise_Hours', 'Calculated_Calorie_Intake',
            'Gender_Female', 'Gender_Male',
            'Disease_Type_Diabetes', 'Disease_Type_Hypertension', 'Disease_Type_Obesity',
            'Dietary_Restrictions_Low_Sodium', 'Dietary_Restrictions_Low_Sugar',
            'Allergies_Gluten', 'Allergies_Peanuts',
            'Preferred_Cuisine_Chinese', 'Preferred_Cuisine_Indian',
            'Preferred_Cuisine_Italian', 'Preferred_Cuisine_Mexican'
        ]
        
        # Create DataFrame for prediction
        input_df = pd.DataFrame([model_input])[encoded_columns]
        print(f"Input DataFrame shape: {input_df.shape}")
        print(f"Input DataFrame:\n{input_df}")
        
        # Make prediction
        prediction = model.predict(input_df)[0]
        print(f"ML Model Prediction: {prediction}")
        
        # Get prediction probability if available
        prediction_proba = None
        if hasattr(model, 'predict_proba'):
            prediction_proba = model.predict_proba(input_df)[0]
            print(f"Prediction probabilities: {prediction_proba}")
        
        # Generate comprehensive diet plan based on prediction and user data
        diet_plan = generate_personalized_diet_plan(model_input, prediction, user_answers, prediction_proba)
        
        return diet_plan
        
    except Exception as e:
        print(f"Error in ML diet plan generation: {e}")
        import traceback
        traceback.print_exc()
        # Use the enhanced fallback that still uses the transformed data
        model_input = transform_diet_answers_to_model_input(user_answers) if 'model_input' not in locals() else model_input
        return generate_enhanced_fallback_diet_plan(user_answers, model_input)

def generate_enhanced_fallback_diet_plan(user_answers: dict, model_input: dict) -> dict:
    """Generate an enhanced diet plan using rule-based logic when ML model is unavailable"""
    
    # Use calculated calories from model_input if available
    calories = int(model_input.get('Calculated_Calorie_Intake', 2000))
    
    # Calculate macros based on health conditions
    if model_input.get('Disease_Type_Diabetes'):
        protein_ratio, carb_ratio, fat_ratio = 0.30, 0.35, 0.35
        health_focus = "Blood Sugar Management"
    elif model_input.get('Disease_Type_Hypertension'):
        protein_ratio, carb_ratio, fat_ratio = 0.25, 0.45, 0.30
        health_focus = "Heart Health & Blood Pressure"
    elif model_input.get('Disease_Type_Obesity'):
        protein_ratio, carb_ratio, fat_ratio = 0.35, 0.35, 0.30
        health_focus = "Weight Management"
    else:
        protein_ratio, carb_ratio, fat_ratio = 0.25, 0.45, 0.30
        health_focus = "General Wellness"
    
    protein_g = int((calories * protein_ratio) / 4)
    carb_g = int((calories * carb_ratio) / 4)
    fat_g = int((calories * fat_ratio) / 9)
    
    # Generate meals based on preferences and restrictions
    meals = generate_meal_suggestions(model_input, user_answers)
    recommendations = generate_health_recommendations(model_input, "rule-based analysis")
    
    return {
        "daily_calories": calories,
        "macros": {
            "protein": f"{protein_g}g",
            "carbs": f"{carb_g}g",
            "fat": f"{fat_g}g"
        },
        "meals": meals,
        "recommendations": recommendations,
        "ml_prediction": "Rule-based recommendation (ML model unavailable)",
        "model_confidence": "Based on established nutritional guidelines",
        "health_focus": health_focus,
        "note": "This plan uses evidence-based nutritional principles. For optimal results, consider consulting with a registered dietitian."
    }

# Rest of the functions remain the same...
def generate_personalized_diet_plan(model_input: dict, prediction: Any, user_answers: dict, prediction_proba=None) -> dict:
    """Generate personalized diet plan based on ML prediction and user data"""
    
    calories = int(model_input['Calculated_Calorie_Intake'])
    
    # Calculate macros based on health conditions and prediction
    if model_input['Disease_Type_Diabetes']:
        # Lower carb for diabetes
        protein_ratio, carb_ratio, fat_ratio = 0.30, 0.35, 0.35
    elif model_input['Disease_Type_Hypertension']:
        # Balanced with focus on heart-healthy fats
        protein_ratio, carb_ratio, fat_ratio = 0.25, 0.45, 0.30
    elif model_input['Disease_Type_Obesity']:
        # Higher protein for weight management
        protein_ratio, carb_ratio, fat_ratio = 0.35, 0.35, 0.30
    else:
        # Standard balanced diet
        protein_ratio, carb_ratio, fat_ratio = 0.25, 0.45, 0.30
    
    protein_g = int((calories * protein_ratio) / 4)  # 4 cal per gram
    carb_g = int((calories * carb_ratio) / 4)        # 4 cal per gram
    fat_g = int((calories * fat_ratio) / 9)          # 9 cal per gram
    
    # Generate meal suggestions based on restrictions and preferences
    meals = generate_meal_suggestions(model_input, user_answers)
    
    # Generate recommendations based on health conditions and ML prediction
    recommendations = generate_health_recommendations(model_input, prediction)
    
    # Create confidence message
    confidence_msg = "Based on AI analysis of your health profile"
    if prediction_proba is not None:
        max_prob = max(prediction_proba)
        confidence_msg += f" (Confidence: {max_prob:.1%})"
    
    diet_plan = {
        "daily_calories": calories,
        "macros": {
            "protein": f"{protein_g}g",
            "carbs": f"{carb_g}g",
            "fat": f"{fat_g}g"
        },
        "meals": meals,
        "recommendations": recommendations,
        "ml_prediction": str(prediction),
        "model_confidence": confidence_msg,
        "health_focus": get_health_focus(model_input)
    }
    
    return diet_plan

def generate_meal_suggestions(model_input: dict, user_answers: dict) -> dict:
    """Generate meal suggestions based on restrictions and preferences"""
    
    # Base meals
    meals = {
        "breakfast": "Oatmeal with fresh fruits and nuts",
        "lunch": "Grilled chicken salad with mixed vegetables",
        "dinner": "Baked salmon with quinoa and steamed broccoli",
        "snacks": ["Greek yogurt", "Apple with almond butter"]
    }
    
    # Modify based on cuisine preferences
    if model_input.get('Preferred_Cuisine_Chinese'):
        meals["lunch"] = "Steamed fish with vegetables and brown rice"
        meals["dinner"] = "Stir-fried tofu with mixed vegetables"
    elif model_input.get('Preferred_Cuisine_Indian'):
        meals["lunch"] = "Dal with vegetables and whole grain roti"
        meals["dinner"] = "Grilled chicken curry with quinoa"
    elif model_input.get('Preferred_Cuisine_Italian'):
        meals["lunch"] = "Grilled chicken with zucchini noodles"
        meals["dinner"] = "Baked fish with herb-roasted vegetables"
    elif model_input.get('Preferred_Cuisine_Mexican'):
        meals["lunch"] = "Grilled fish tacos with cabbage slaw"
        meals["dinner"] = "Chicken and bean bowl with avocado"
    
    # Modify based on dietary restrictions
    if model_input.get('Dietary_Restrictions_Low_Sodium'):
        meals["breakfast"] = "Fresh fruit bowl with unsalted nuts"
        meals["lunch"] = "Herb-seasoned grilled protein with fresh salad"
        meals["snacks"] = ["Fresh fruits", "Unsalted nuts"]
    
    if model_input.get('Dietary_Restrictions_Low_Sugar'):
        meals["breakfast"] = "Scrambled eggs with spinach and avocado"
        meals["snacks"] = ["Nuts and seeds", "Cucumber with hummus"]
    
    # Modify based on allergies
    if model_input.get('Allergies_Gluten'):
        meals["breakfast"] = "Gluten-free oatmeal with berries"
        meals["lunch"] = "Quinoa bowl with grilled protein"
    
    if model_input.get('Allergies_Peanuts'):
        meals["snacks"] = ["Greek yogurt", "Apple slices", "Sunflower seeds"]
    
    return meals

def generate_health_recommendations(model_input: dict, prediction: Any) -> list:
    """Generate health recommendations based on model input and prediction"""
    recommendations = [
        "Drink at least 8 glasses of water daily",
        "Eat meals every 3-4 hours to maintain stable energy"
    ]
    
    # Add condition-specific recommendations
    if model_input.get('Disease_Type_Diabetes'):
        recommendations.extend([
            "Monitor blood sugar levels regularly",
            "Choose complex carbohydrates over simple sugars",
            "Include fiber-rich foods in every meal",
            "Avoid sugary drinks and processed foods"
        ])
    
    if model_input.get('Disease_Type_Hypertension'):
        recommendations.extend([
            "Limit sodium intake to less than 2300mg daily",
            "Include potassium-rich foods like bananas and spinach",
            "Practice portion control",
            "Reduce processed and packaged foods"
        ])
    
    if model_input.get('Disease_Type_Obesity'):
        recommendations.extend([
            "Focus on portion control and mindful eating",
            "Increase physical activity gradually",
            "Keep a food diary to track intake",
            "Choose lean proteins and whole grains"
        ])
    
    # Activity-based recommendations
    activity_level = model_input.get('Physical_Activity_Level', 1)
    if activity_level >= 2:
        recommendations.append("Include post-workout protein within 30 minutes of exercise")
    elif activity_level == 0:
        recommendations.append("Consider adding light physical activity like walking")
    
    # Add prediction-based recommendations
    recommendations.append(f"Based on your profile analysis: {prediction}")
    
    return recommendations

def get_health_focus(model_input: dict) -> str:
    """Determine the main health focus based on conditions"""
    if model_input.get('Disease_Type_Diabetes'):
        return "Blood Sugar Management"
    elif model_input.get('Disease_Type_Hypertension'):
        return "Heart Health & Blood Pressure"
    elif model_input.get('Disease_Type_Obesity'):
        return "Weight Management"
    else:
        return "General Wellness"

# Fitness plan generation (existing code remains the same)
def generate_fitness_plan(user_answers: dict) -> dict:
    """Generate fitness plan based on user answers"""
    # Extract key information
    age = user_answers.get("Q1", "Unknown")  # age
    fitness_level = user_answers.get("Q2", "Beginner")  # fitness level
    goal = user_answers.get("Q3", "General fitness")  # fitness goal
    available_days = user_answers.get("Q4", "3")  # days per week
    session_duration = user_answers.get("Q5", "45 min")  # session duration
    workout_location = user_answers.get("Q6", "home")  # gym or home
    injuries = user_answers.get("Q7", "None")  # injuries
    preferred_exercises = user_answers.get("Q8", "mixed")  # exercise preferences
    
    fitness_plan = {
        "workout_days_per_week": int(available_days) if available_days.isdigit() else 3,
        "workout_duration": session_duration,
        "weekly_schedule": generate_workout_schedule(available_days, goal, fitness_level, workout_location),
        "recommendations": generate_fitness_recommendations(goal, fitness_level, injuries)
    }
    
    return fitness_plan

def generate_workout_schedule(days, goal, level, location):
    return {
        "monday": {"type": "Upper Body", "exercises": ["Push-ups", "Pull-ups"]},
        "wednesday": {"type": "Cardio", "exercises": ["Running", "Cycling"]},
        "friday": {"type": "Lower Body", "exercises": ["Squats", "Lunges"]}
    }

def generate_fitness_recommendations(goal, level, injuries):
    return ["Start with lighter weights", "Focus on proper form"]

def format_plan_response(plan: dict, plan_type: str) -> str:
    """Format plan dictionary into readable text"""
    if plan_type == "diet":
        response = f"""Here's your personalized diet plan:

🎯 Health Focus: {plan.get('health_focus', 'General Wellness')}
📊 Daily Calories: {plan['daily_calories']}
🍽️ Macros: Protein {plan['macros']['protein']}, Carbs {plan['macros']['carbs']}, Fat {plan['macros']['fat']}

🥘 Meals:
• Breakfast: {plan['meals']['breakfast']}
• Lunch: {plan['meals']['lunch']}
• Dinner: {plan['meals']['dinner']}"""
        
        if 'snacks' in plan['meals']:
            response += f"\n• Snacks: {', '.join(plan['meals']['snacks'])}"
        
        response += f"\n\n💡 Key Recommendations:\n"
        for i, rec in enumerate(plan['recommendations'][:3], 1):  # Show top 3
            response += f"{i}. {rec}\n"
        
        if 'model_confidence' in plan:
            response += f"\n✨ {plan['model_confidence']}"
        
        return response
    
    else:  # fitness
        return f"""Here's your personalized fitness plan:

Workout Schedule: {plan['workout_days_per_week']} days per week, {plan['workout_duration']} each

Weekly Plan:
""" + "\n".join([f"- {day.title()}: {details['type']}" 
                 for day, details in plan['weekly_schedule'].items()]) + f"""

Recommendations: {', '.join(plan['recommendations'])}"""