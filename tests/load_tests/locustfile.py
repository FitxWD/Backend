from locust import HttpUser, task, between, TaskSet, events
import json
import os
import random
from datetime import datetime
from firebase_utils import initialize_firebase, create_test_user, delete_test_user

# Initialize Firebase Admin
initialize_firebase()

DIET_QUESTIONS = [
    {"id": "age", "type": "number"},
    {"id": "gender", "type": "select", "options": ["Male", "Female"]},
    {"id": "height", "type": "number"},
    {"id": "weight", "type": "number"},
    {"id": "healthConditions", "type": "select", "options": ["Diabetes", "Hypertension", "Obesity", "None"]},
    {"id": "conditionSeverity", "type": "select", "options": ["Mild", "Moderate", "Severe"]},
    {"id": "activityLevel", "type": "select", "options": ["Sedentary", "Moderate", "Active"]},
    {"id": "cholesterolLevel", "type": "text"},
    {"id": "bloodPressure", "type": "text"},
    {"id": "glucoseLevel", "type": "text"},
    {"id": "dietaryRestrictions", "type": "select", "options": ["Low Sodium", "Low Sugar", "None"]},
    {"id": "foodAllergies", "type": "select", "options": ["Gluten", "Peanuts", "None"]},
    {"id": "cuisinePreference", "type": "select", "options": ["Chinese", "Indian", "Italian", "Mexican"]},
    {"id": "exerciseHours", "type": "number"}
]

class UserBehavior(TaskSet):
    def on_start(self):
        """Setup for user session"""
        # Create real Firebase user and get token
        self.user_id, self.token = create_test_user()
        if not self.user_id or not self.token:
            raise Exception("Failed to create test user")

        # Set proper Authorization header
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        print(f"🔑 Created test user {self.user_id} with token header: Bearer {self.token[:20]}...")
        
        # Test data
        self.diet_plan_ids = [
            "Balanced_1700", "Balanced_2100", "Balanced_2500",
            "Low_Carb_1900", "Low_Carb_2300",
            "Low_Sodium_2100", "Low_Sodium_2500"
        ]
        
        # Add catch_response=True to initial profile creation
        with self.client.post(
            "/api/v1/profile-health-update",
            headers=self.headers,
            json={
                "healthData": {
                    "gender": "male",
                    "age": 25,
                    "weight": 70,
                    "height": 175
                },
                "is_test_user": True,
                "created_at": datetime.utcnow().isoformat()
            },
            name="[Setup] Create Test User",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                print(f"✅ Created initial profile for {self.user_id}")
                response.success()
            else:
                print(f"❌ Profile creation failed: {response.text}")
                print(f"Headers used: {self.headers}")
                response.failure(f"Failed to create profile: {response.text}")

    @task(2)
    def get_profile(self):
        """Test profile endpoint"""
        with self.client.get(
            "/api/v1/profile",
            headers=self.headers,
            name="/profile",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Profile Error: {response.text}")
                print(f"Failed profile request with token: {self.token[:20]}...")

    @task(3)
    def generate_diet_plan(self):
        """Test diet plan generation with frontend data format"""
        # Generate form data first
        form_data = {
            "age": str(random.randint(18, 65)),
            "gender": random.choice(["Male", "Female"]),
            "height": str(random.randint(150, 190)),
            "weight": str(random.randint(45, 100)),
            "healthConditions": random.choice(["Diabetes", "Hypertension", "Obesity", "None"]),
            "conditionSeverity": random.choice(["Mild", "Moderate", "Severe"]),
            "activityLevel": random.choice(["Sedentary", "Moderate", "Active"]),
            "cholesterolLevel": random.choice(["200", "Don't know"]),
            "bloodPressure": random.choice(["120/80", "Don't know"]),
            "glucoseLevel": random.choice(["100", "Don't know"]),
            "dietaryRestrictions": random.choice(["Low Sodium", "Low Sugar", "None"]),
            "foodAllergies": random.choice(["Gluten", "Peanuts", "None"]),
            "cuisinePreference": random.choice(["Chinese", "Indian", "Italian", "Mexican"]),
            "exerciseHours": str(random.randint(1, 10))
        }
        
        # Transform data to match frontend format (Q0, Q1, etc.)
        transformed_data = {
            f"Q{index}": form_data[question["id"]]
            for index, question in enumerate(DIET_QUESTIONS)
        }
        
        payload = {
            "plan_type": "diet",
            "user_answers": transformed_data,
            "user_id": self.user_id
        }
        
        with self.client.post(
            "/api/v1/generate-plan",
            headers=self.headers,
            json=payload,
            name="/generate-plan",
            catch_response=True  # Added catch_response
        ) as response:
            if response.status_code == 200:
                self.plan_data = response.json()
                response.success()
            else:
                response.failure(f"Generate Plan Error: {response.text}")

    @task(1)
    def accept_plan(self):
        """Test plan acceptance"""
        payload = {
            "plan_id": random.choice(self.diet_plan_ids),
            "plan_type": "diet",
            "user_id": self.user_id,
            "accepted": random.choice([True, False])
        }
        
        with self.client.post(
            "/api/v1/accept-plan",
            headers=self.headers,
            json=payload,
            name="/accept-plan",
            catch_response=True  # Added catch_response
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Accept Plan Error: {response.text}")

    @task(1)
    def get_diet_plan_details(self):
        """Test getting diet plan details"""
        plan_id = random.choice(self.diet_plan_ids)
        with self.client.get(
            f"/api/v1/diet-plan/{plan_id}",
            headers=self.headers,
            name="/diet-plan",
            catch_response=True  # Added catch_response
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Diet Plan Details Error: {response.text}")

    @task(1)
    def update_health_profile(self):
        """Test health profile updates"""
        payload = {
            "healthData": {
                "gender": random.choice(["male", "female"]).lower(),  # Changed to lowercase
                "age": random.randint(18, 65),
                "weight": round(random.uniform(50, 100), 1),
                "height": round(random.uniform(150, 190), 1)
            }
        }
        
        with self.client.post(
            "/api/v1/profile-health-update",
            headers=self.headers,
            json=payload,
            name="/profile-health-update",
            catch_response=True  # Added catch_response
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health Profile Update Error: {response.text}")

    def on_stop(self):
        """Cleanup when user stops"""
        try:
            # Delete the Firebase Auth user
            delete_test_user(self.user_id)
        except Exception as e:
            print(f"Error in cleanup: {e}")

class ApiUser(HttpUser):
    tasks = [UserBehavior]
    wait_time = between(1, 3)