import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.voice_service.plan_generator import (
    transform_fitness_answers_to_model_input, 
    generate_fitness_plan,
    get_fitness_model
)

def test_fitness_model_prediction():
    """Test fitness model with various sample user answers"""
    
    print("=" * 60)
    print("TESTING FITNESS MODEL PREDICTIONS")
    print("=" * 60)
    
    # Test Case 1: Beginner Male
    print("\n[TEST 1] Beginner Male Profile")
    print("-" * 40)
    
    beginner_male_answers = {
        "Q0": "25",  # Age
        "Q1": "Male",  # Gender
        "Q2": "175",  # Height in cm
        "Q3": "70",  # Weight in kg
        "Q4": "7",  # Sleep hours
        "Q5": "2.5",  # Water intake in litres
        "Q6": "8000",  # Daily steps
        "Q7": "70",  # Resting heart rate
        "Q8": "120",  # Systolic BP
        "Q9": "80",  # Diastolic BP
        "Q10": "beginner",  # Fitness level
        "Q11": "30",  # Workout duration
        "Q12": "moderate",  # Workout intensity
        "Q13": "average",  # Endurance level
        "Q14": "5",  # Stress level (1-10)
        "Q15": "non-smoker",  # Smoking status
        "Q16": "None of the above"  # Health conditions
    }
    
    try:
        prediction = generate_fitness_plan(beginner_male_answers)
        print(f"PREDICTION SUCCESS: {prediction['ml_prediction']}")
        print(f"User Summary: {prediction['user_input_summary']}")
        print(f"Model Type: {prediction['model_info']['model_type']}")
    except Exception as e:
        print(f"PREDICTION FAILED: {e}")
    
    try:
        prediction = generate_fitness_plan(low_fitness_answers)
        print(f" PREDICTION SUCCESS: {prediction['ml_prediction']}")
        print(f"   User Summary: {prediction['user_input_summary']}")
        print(f"   Model Type: {prediction['model_info']['model_type']}")
    except Exception as e:
        print(f" PREDICTION FAILED: {e}")
    
    # Test Case 5: Edge Case - Very Young and Fit
    print("\n[TEST 5] Young Athletic Profile")
    print("-" * 40)
    
    young_athletic_answers = {
        "Q0": "20",  # Age
        "Q1": "Male",  # Gender
        "Q2": "185",  # Height in cm
        "Q3": "75",  # Weight in kg
        "Q4": "9",  # Sleep hours
        "Q5": "4",  # Water intake in litres
        "Q6": "15000",  # Daily steps
        "Q7": "50",  # Resting heart rate
        "Q8": "110",  # Systolic BP
        "Q9": "65",  # Diastolic BP
        "Q10": "advanced",  # Fitness level
        "Q11": "90",  # Workout duration
        "Q12": "high",  # Workout intensity
        "Q13": "high",  # Endurance level
        "Q14": "2",  # Stress level (1-10)
        "Q15": "non-smoker",  # Smoking status
        "Q16": "None of the above"  # Health conditions
    }
    
    try:
        prediction = generate_fitness_plan(young_athletic_answers)
        print(f" PREDICTION SUCCESS: {prediction['ml_prediction']}")
        print(f"   User Summary: {prediction['user_input_summary']}")
        print(f"   Model Type: {prediction['model_info']['model_type']}")
    except Exception as e:
        print(f" PREDICTION FAILED: {e}")

def test_model_loading():
    """Test if the fitness model loads correctly"""
    print("\n[MODEL LOADING TEST]")
    print("-" * 40)
    
    try:
        model = get_fitness_model()
        if model is not None:
            print(f" Model loaded successfully: {type(model)}")
            print(f"   Model has predict method: {hasattr(model, 'predict')}")
            
            # Try to get model info
            if hasattr(model, 'feature_names_in_'):
                print(f"   Expected features: {len(model.feature_names_in_)}")
            if hasattr(model, 'n_features_in_'):
                print(f"   Feature count: {model.n_features_in_}")
                
        else:
            print(" Model failed to load")
            
    except Exception as e:
        print(f" Model loading error: {e}")

def test_transformation_only():
    """Test just the transformation function without prediction"""
    print("\n[TRANSFORMATION TEST]")
    print("-" * 40)
    
    sample_answers = {
        "Q0": "25",  # Age
        "Q1": "Female",  # Gender
        "Q2": "170",  # Height
        "Q3": "65",  # Weight
        "Q4": "8",  # Sleep
        "Q5": "2.5",  # Water
        "Q6": "10000",  # Steps
        "Q7": "65",  # HR
        "Q8": "115",  # Systolic
        "Q9": "75",  # Diastolic
        "Q10": "intermediate",  # Fitness
        "Q11": "45",  # Duration
        "Q12": "moderate",  # Intensity
        "Q13": "average",  # Endurance
        "Q14": "4",  # Stress
        "Q15": "non-smoker",  # Smoking
        "Q16": "None of the above"  # Conditions
    }
    
    try:
        transformed = transform_fitness_answers_to_model_input(sample_answers)
        print("✅ Transformation successful")
        print("   Key features:")
        for key, value in transformed.items():
            if key in ['age', 'weight_kg', 'height_cm', 'bmi', 'fitness_level', 'intensity']:
                print(f"     {key}: {value}")
        
        # Check all required columns are present
        required_cols = [
            'age', 'height_cm', 'weight_kg', 'bmi', 'duration_minutes', 'intensity',
            'calories_burned', 'daily_steps', 'resting_heart_rate',
            'blood_pressure_systolic', 'blood_pressure_diastolic',
            'endurance_level', 'sleep_hours', 'stress_level', 'hydration_level',
            'fitness_level', 'gender_F', 'gender_M', 'smoking_status_Current',
            'smoking_status_Former', 'health_condition_Asthma',
            'health_condition_Diabetes', 'health_condition_Hypertension'
        ]
        
        missing_cols = [col for col in required_cols if col not in transformed]
        if missing_cols:
            print(f" Missing columns: {missing_cols}")
        else:
            print(" All required columns present")
            
    except Exception as e:
        print(f" Transformation failed: {e}")

def run_all_tests():
    """Run all fitness model tests"""
    print("FITNESS MODEL TESTING SUITE")
    print("=" * 60)
    
    # Test 1: Model loading
    test_model_loading()
    
    # Test 2: Transformation only
    test_transformation_only()
    
    # Test 3: Full predictions
    test_fitness_model_prediction()
    
    print("\n" + "=" * 60)
    print("FITNESS MODEL TESTING COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    run_all_tests()