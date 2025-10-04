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
    """Generate diet plan using ML model prediction only"""
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
    
    return prediction

# Fitness plan generation 
def generate_fitness_plan(user_answers: dict) -> dict:
    """Generate fitness plan based on user answers"""
    fitness_plan = "..."
    return fitness_plan