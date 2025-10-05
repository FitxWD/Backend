# backend/tests/test_plans_api.py

import pytest
import requests
import os

BACKEND_API_URL = os.getenv("BACKEND_API_URL")

def test_get_valid_diet_plan():
    """Tests fetching a known, valid diet plan."""
    plan_id = "Balanced_1700"
    response = requests.get(f"{BACKEND_API_URL}/api/v1/diet-plan/{plan_id}")
    
    assert response.status_code == 200
    plan_data = response.json()
    assert plan_data["diet_type"] == "Balanced"
    assert "days" in plan_data

def test_get_invalid_diet_plan():
    """Tests that fetching a non-existent plan returns a 404 error."""
    plan_id = "Non_Existent_Plan"
    response = requests.get(f"{BACKEND_API_URL}/api/v1/diet-plan/{plan_id}")

    assert response.status_code == 404
    error_data = response.json()
    assert error_data["detail"] == "Diet plan not found"

def test_get_valid_workout_plan():
    """Tests fetching a known, valid workout plan."""
    plan_id = "gentle_start"
    response = requests.get(f"{BACKEND_API_URL}/api/v1/workout-plan/{plan_id}")
    
    assert response.status_code == 200
    plan_data = response.json()
    assert plan_data["name"] == "Gentle Start"
    assert "weekly_template" in plan_data

def test_get_invalid_workout_plan():
    """Tests fetching a non-existent workout plan returns a 404 error."""
    plan_id = "Non_Existent_Workout_Plan"
    response = requests.get(f"{BACKEND_API_URL}/api/v1/workout-plan/{plan_id}")

    assert response.status_code == 404
    error_data = response.json()
    assert error_data["detail"] == "Workout plan not found"