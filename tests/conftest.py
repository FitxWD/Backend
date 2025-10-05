import pytest
import requests
import os
from dotenv import load_dotenv
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app 

env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

@pytest.fixture(scope="session")
def auth_token():
    """Logs in a test user to Firebase and returns a fresh ID token."""
    api_key = os.getenv("FIREBASE_API_KEY")
    email = os.getenv("TEST_USER_EMAIL")
    password = os.getenv("TEST_USER_PASSWORD")

    # These assertions will now pass because the .env file was loaded above.
    assert api_key, "FIREBASE_API_KEY not found in .env file"
    assert email, "TEST_USER_EMAIL not found in .env file"
    assert password, "TEST_USER_PASSWORD not found in .env file"

    signin_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"
    payload = {"email": email, "password": password, "returnSecureToken": True}
    
    response = requests.post(signin_url, json=payload)
    response.raise_for_status() 
    
    data = response.json()
    print("\nSuccessfully fetched a fresh Firebase auth token.")
    return data["idToken"]

@pytest.fixture
def auth_headers(auth_token):
    """A fixture that uses the fresh token to create authorization headers."""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }

@pytest.fixture(scope="module")
def client():
    """
    A fixture that provides a FastAPI TestClient for making API calls
    without needing a running server.
    """
    with TestClient(app) as c:
        yield c