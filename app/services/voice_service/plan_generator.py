import pickle
import pandas as pd
import numpy as np
import os
from typing import Dict, Any
import joblib  # Alternative to pickle

# Load the saved diet model
def load_diet_model():
    """Load the saved diet prediction model"""
    model_path = "models/diet_model.joblib"
    
    try:
        if os.path.exists(model_path):
            print(f"Trying to load model from: {model_path}")
            model = joblib.load(model_path)
            print(f"Diet model loaded successfully from: {model_path}")
            print(f"Model type: {type(model)}")
            return model
        else:
            print(f"Model file not found: {model_path}")
            return None
                
    except Exception as e:
        print(f"Error loading model from {model_path}: {e}")
        return None

# Global model instance
_diet_model = None

def get_diet_model():
    global _diet_model
    if _diet_model is None:
        _diet_model = load_diet_model()
    return _diet_model

def load_fitness_model():
    """Load the saved fitness prediction model"""
    model_path = "models/fitness_model.joblib"
    
    try:
        if os.path.exists(model_path):
            print(f"Trying to load fitness model from: {model_path}")
            model = joblib.load(model_path)
            print(f"Fitness model loaded successfully from: {model_path}")
            print(f"Model type: {type(model)}")
            return model
        else:
            print(f"Fitness model file not found: {model_path}")
            return None
                
    except Exception as e:
        print(f"Error loading fitness model from {model_path}: {e}")
        return None

# Global fitness model instance
_fitness_model = None

def get_fitness_model():
    global _fitness_model
    if _fitness_model is None:
        _fitness_model = load_fitness_model()
    return _fitness_model

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

def transform_fitness_answers_to_model_input(user_answers: dict) -> dict:
    """Transform user answers to match the fitness model's expected input format"""
    
    # Initialize the feature dictionary with all columns set to 0
    encoded_columns = [
        'age', 'height_cm', 'weight_kg', 'bmi', 'duration_minutes', 'intensity',
        'calories_burned', 'daily_steps', 'resting_heart_rate',
        'blood_pressure_systolic', 'blood_pressure_diastolic',
        'endurance_level', 'sleep_hours', 'stress_level', 'hydration_level',
        'fitness_level', 'gender_F', 'gender_M', 'smoking_status_Current',
        'smoking_status_Former', 'health_condition_Asthma',
        'health_condition_Diabetes', 'health_condition_Hypertension'
    ]
    
    # Initialize all features to 0
    features = {col: 0 for col in encoded_columns}
    
    print(f"Debug - Input fitness answers: {user_answers}")
    
    # Extract and transform answers based on fitness questions (Q0-Q16)
    
    # Q0: Age - "First, may I know your age?"
    age = extract_number(user_answers.get("Q0", "25"))
    features['age'] = age
    print(f"Debug - Age: {age}")
    
    # Q1: Gender - "What is your gender? (Male, Female, or Other)"
    gender = user_answers.get("Q1", "").lower()
    if "female" in gender:
        features['gender_F'] = 1
        features['gender_M'] = 0
    elif "male" in gender:
        features['gender_M'] = 1
        features['gender_F'] = 0
    else:  # Other or unknown, default to male
        features['gender_M'] = 1
        features['gender_F'] = 0
    print(f"Debug - Gender: {gender}, Female: {features['gender_F']}, Male: {features['gender_M']}")
    
    # Q2: Height - "Could you tell me your height in centimeters?"
    height = extract_number(user_answers.get("Q2", "170"))
    features['height_cm'] = height
    print(f"Debug - Height: {height}")
    
    # Q3: Weight - "And your weight in kilograms?"
    weight = extract_number(user_answers.get("Q3", "70"))
    features['weight_kg'] = weight
    print(f"Debug - Weight: {weight}")
    
    # Calculate BMI
    height_m = height / 100
    bmi = weight / (height_m ** 2) if height_m > 0 else 25
    features['bmi'] = bmi
    print(f"Debug - BMI: {bmi}")
    
    # Q4: Sleep hours - "How many hours of sleep do you usually get per day?"
    sleep_hours = extract_number(user_answers.get("Q4", "8"))
    features['sleep_hours'] = sleep_hours
    print(f"Debug - Sleep hours: {sleep_hours}")
    
    # Q5: Water intake - "How many litres of water do you usually drink in a day?"
    water_intake = extract_number(user_answers.get("Q5", "2"))
    features['hydration_level'] = water_intake
    print(f"Debug - Water intake: {water_intake}")
    
    # Q6: Daily steps - "How many steps do you usually take in a day?"
    daily_steps = extract_number(user_answers.get("Q6", "8000"))
    features['daily_steps'] = daily_steps
    print(f"Debug - Daily steps: {daily_steps}")
    
    # Q7: Resting heart rate - "What's your resting heart rate (in beats per minute)?"
    resting_hr = extract_number(user_answers.get("Q7", "70"))
    features['resting_heart_rate'] = resting_hr if resting_hr > 0 else 70
    print(f"Debug - Resting HR: {resting_hr}")
    
    # Q8: Systolic BP - "What's your systolic blood pressure? (the higher number, e.g., 120)"
    systolic_bp = extract_number(user_answers.get("Q8", "120"))
    features['blood_pressure_systolic'] = systolic_bp if systolic_bp > 0 else 120
    print(f"Debug - Systolic BP: {systolic_bp}")
    
    # Q9: Diastolic BP - "What's your diastolic blood pressure? (the lower number, e.g., 80)"
    diastolic_bp = extract_number(user_answers.get("Q9", "80"))
    features['blood_pressure_diastolic'] = diastolic_bp if diastolic_bp > 0 else 80
    print(f"Debug - Diastolic BP: {diastolic_bp}")
    
    # Q10: Fitness level - "How would you describe your overall fitness level — beginner, intermediate, or advanced?"
    fitness_level = user_answers.get("Q10", "").lower()
    if "beginner" in fitness_level:
        features['fitness_level'] = 0
    elif "intermediate" in fitness_level:
        features['fitness_level'] = 1
    elif "advanced" in fitness_level:
        features['fitness_level'] = 2
    else:
        features['fitness_level'] = 0  # Default to beginner
    print(f"Debug - Fitness level: {fitness_level}, mapped to: {features['fitness_level']}")
    
    # Q11: Workout duration - "Have you done any workouts? If so, on average, how long do your workout sessions last? (in minutes)"
    workout_duration = extract_number(user_answers.get("Q11", "30"))
    features['duration_minutes'] = workout_duration
    print(f"Debug - Workout duration: {workout_duration}")
    
    # Q12: Workout intensity - "How would you describe your workout intensity — low, moderate, or high?"
    intensity = user_answers.get("Q12", "").lower()
    if "low" in intensity:
        features['intensity'] = 0
    elif "moderate" in intensity:
        features['intensity'] = 1
    elif "high" in intensity:
        features['intensity'] = 2
    else:
        features['intensity'] = 1  # Default to moderate
    print(f"Debug - Intensity: {intensity}, mapped to: {features['intensity']}")
    
    # Q13: Endurance level - "How would you rate your endurance level — low, average, or high?"
    endurance = user_answers.get("Q13", "").lower()
    if "low" in endurance:
        features['endurance_level'] = 0
    elif "average" in endurance:
        features['endurance_level'] = 1
    elif "high" in endurance:
        features['endurance_level'] = 2
    else:
        features['endurance_level'] = 1  # Default to average
    print(f"Debug - Endurance: {endurance}, mapped to: {features['endurance_level']}")
    
    # Q14: Stress level - "On a scale of 1–10, how would you rate your current stress level?"
    stress_level = extract_number(user_answers.get("Q14", "5"))
    features['stress_level'] = stress_level if 1 <= stress_level <= 10 else 5
    print(f"Debug - Stress level: {stress_level}")
    
    # Q15: Smoking status - "What's your smoking status — current smoker, former smoker, or non-smoker?"
    smoking = user_answers.get("Q15", "").lower()
    if "current" in smoking:
        features['smoking_status_Current'] = 1
        features['smoking_status_Former'] = 0
    elif "former" in smoking:
        features['smoking_status_Former'] = 1
        features['smoking_status_Current'] = 0
    else:  # Non-smoker or other
        features['smoking_status_Current'] = 0
        features['smoking_status_Former'] = 0
    print(f"Debug - Smoking: {smoking}, Current: {features['smoking_status_Current']}, Former: {features['smoking_status_Former']}")
    
    # Q16: Health conditions - "Do you have any of the following health conditions such as Asthma, Diabetes, Hypertension, or None of the above?"
    conditions = user_answers.get("Q16", "").lower()
    if "asthma" in conditions:
        features['health_condition_Asthma'] = 1
    if "diabetes" in conditions:
        features['health_condition_Diabetes'] = 1
    if "hypertension" in conditions or "blood pressure" in conditions:
        features['health_condition_Hypertension'] = 1
    print(f"Debug - Health conditions: {conditions}")
    
    # Calculate estimated calories burned based on fitness data
    # Basic METs calculation for moderate activity
    if features['duration_minutes'] > 0:
        # Estimate METs based on intensity: low=3, moderate=5, high=8
        mets = {0: 3, 1: 5, 2: 8}.get(features['intensity'], 5)
        # Calories = METs × weight (kg) × time (hours)
        hours = features['duration_minutes'] / 60
        estimated_calories = mets * features['weight_kg'] * hours
        features['calories_burned'] = int(estimated_calories)
    else:
        features['calories_burned'] = 0
    
    print(f"Debug - Estimated calories burned: {features['calories_burned']}")
    print(f"Final transformed fitness features: {features}")
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
    """Generate diet plan showing only ML model prediction number"""
    print(f"Generating diet plan with answers: {user_answers}")
    
    # Transform answers to model input format
    model_input = transform_diet_answers_to_model_input(user_answers)
    
    # Load the ML model - if it fails, return error instead of fallback
    model = get_diet_model()
    if model is None:
        raise Exception("ML model not available - cannot generate diet plan")
    
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
    
    # Return just the prediction number and basic info
    return {
        "ml_prediction": int(prediction),
        "user_input_summary": {
            "age": model_input['Age'],
            "weight": model_input['Weight_kg'],
            "height": model_input['Height_cm'],
            "bmi": round(model_input['BMI'], 2),
            "gender": "Female" if model_input['Gender_Female'] else "Male",
            "calories": model_input['Calculated_Calorie_Intake']
        },
        "model_info": {
            "model_type": str(type(model).__name__),
            "features_count": len(encoded_columns)
        }
    }

def generate_fitness_plan(user_answers: dict) -> dict:
    """Generate fitness plan showing only ML model prediction number"""
    print(f"Generating fitness plan with answers: {user_answers}")
    
    # Transform answers to model input format
    model_input = transform_fitness_answers_to_model_input(user_answers)
    
    # Load the ML model - if it fails, return error instead of fallback
    model = get_fitness_model()  # You'll need to create this function similar to get_diet_model()
    if model is None:
        raise Exception("ML fitness model not available - cannot generate fitness plan")
    
    # Prepare input for prediction
    encoded_columns = [
        'age', 'height_cm', 'weight_kg', 'bmi', 'duration_minutes', 'intensity',
        'calories_burned', 'daily_steps', 'resting_heart_rate',
        'blood_pressure_systolic', 'blood_pressure_diastolic',
        'endurance_level', 'sleep_hours', 'stress_level', 'hydration_level',
        'fitness_level', 'gender_F', 'gender_M', 'smoking_status_Current',
        'smoking_status_Former', 'health_condition_Asthma',
        'health_condition_Diabetes', 'health_condition_Hypertension'
    ]
    
    # Create DataFrame for prediction
    input_df = pd.DataFrame([model_input])[encoded_columns]
    print(f"Fitness Input DataFrame shape: {input_df.shape}")
    print(f"Fitness Input DataFrame:\n{input_df}")
    
    # Make prediction
    prediction = model.predict(input_df)[0]
    print(f"Fitness ML Model Prediction: {prediction}")
    
    # Return just the prediction number and basic info
    return {
        "ml_prediction": int(prediction),
        "user_input_summary": {
            "age": model_input['age'],
            "weight": model_input['weight_kg'],
            "height": model_input['height_cm'],
            "bmi": round(model_input['bmi'], 2),
            "gender": "Female" if model_input['gender_F'] else "Male",
            "fitness_level": ["Beginner", "Intermediate", "Advanced"][model_input['fitness_level']],
            "workout_duration": model_input['duration_minutes'],
            "intensity": ["Low", "Moderate", "High"][model_input['intensity']],
            "daily_steps": model_input['daily_steps'],
            "sleep_hours": model_input['sleep_hours'],
            "stress_level": model_input['stress_level']
        },
        "model_info": {
            "model_type": str(type(model).__name__),
            "features_count": len(encoded_columns)
        }
    }

def format_plan_response(plan: dict, plan_type: str) -> str:
    """Format plan dictionary into readable text"""
    if plan_type == "diet":
        response = f"""ML Model Prediction: {plan['ml_prediction']}

User Profile:
• Age: {plan['user_input_summary']['age']} years
• Gender: {plan['user_input_summary']['gender']}
• Weight: {plan['user_input_summary']['weight']} kg
• Height: {plan['user_input_summary']['height']} cm
• BMI: {plan['user_input_summary']['bmi']}
• Calculated Calories: {plan['user_input_summary']['calories']}

Model Information:
• Model Type: {plan['model_info']['model_type']}
• Features Used: {plan['model_info']['features_count']}"""
        
        return response
    
    elif plan_type == "fitness":
        response = f"""ML Model Prediction: {plan['ml_prediction']}

User Profile:
• Age: {plan['user_input_summary']['age']} years
• Gender: {plan['user_input_summary']['gender']}
• Weight: {plan['user_input_summary']['weight']} kg
• Height: {plan['user_input_summary']['height']} cm
• BMI: {plan['user_input_summary']['bmi']}
• Fitness Level: {plan['user_input_summary']['fitness_level']}
• Workout Duration: {plan['user_input_summary']['workout_duration']} minutes
• Intensity: {plan['user_input_summary']['intensity']}
• Daily Steps: {plan['user_input_summary']['daily_steps']}
• Sleep Hours: {plan['user_input_summary']['sleep_hours']}
• Stress Level: {plan['user_input_summary']['stress_level']}/10

Model Information:
• Model Type: {plan['model_info']['model_type']}
• Features Used: {plan['model_info']['features_count']}"""
        
        return response
    
    else:
        return f"Unknown plan type: {plan_type}"