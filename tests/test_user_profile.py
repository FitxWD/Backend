import pytest
import requests
import os

BACKEND_API_URL = os.getenv("BACKEND_API_URL")
TEST_USER_ID = os.getenv("TEST_USER_ID")

# --- Test Cases ---

def test_get_my_profile(auth_headers):
    """
    Tests the /profile endpoint to ensure authentication is working and returns data.
    """
    response = requests.get(f"{BACKEND_API_URL}/api/v1/profile", headers=auth_headers)
    
    # Assert that the request was successful
    assert response.status_code == 200
    
    # Assert that the response contains expected user data
    profile_data = response.json()
    assert "email" in profile_data
    assert "name" in profile_data
    print(f"Successfully fetched profile for user: {profile_data['email']}")


def test_onboarding_health_data_update_and_verify(auth_headers):
    """
    This is the core onboarding test. It first updates the user's health data,
    then immediately tries to fetch it back to verify the write was successful.
    """
    # --- STAGE 1: UPDATE HEALTH DATA (The Onboarding Step) ---
    
    health_data_payload = {
        "healthData": {
            "gender": "female",
            "age": 28,
            "weight": 65,
            "height": 170
        }
    }

    update_response = requests.post(
        f"{BACKEND_API_URL}/api/v1/profile-health-update", 
        json=health_data_payload, 
        headers=auth_headers
    )

    # Assert that the POST request was successful
    assert update_response.status_code == 200
    assert update_response.json() == {"ok": True}
    print("Successfully submitted health data.")
    
    # --- STAGE 2: VERIFY THE DATA WAS SAVED ---
    
    verify_response = requests.get(
        f"{BACKEND_API_URL}/api/v1/user-health-data/{TEST_USER_ID}", 
        headers=auth_headers
    )

    # Assert that the GET request was successful
    assert verify_response.status_code == 200
    
    # Assert that the data we just sent is now stored
    retrieved_data = verify_response.json()
    assert retrieved_data["gender"] == "female"
    assert retrieved_data["age"] == 28
    print("Successfully verified that the health data was saved correctly.")