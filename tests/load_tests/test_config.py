import os
from firebase_admin import credentials, initialize_app

# Test configuration
TEST_SETTINGS = {
    "FIRESTORE_EMULATOR_HOST": "localhost:8080",
    "TESTING": "true",
    "PROJECT_ID": "test-project"
}

def setup_test_env():
    """Setup test environment variables"""
    for key, value in TEST_SETTINGS.items():
        os.environ[key] = value

    # Initialize Firebase with emulator
    if os.getenv("FIRESTORE_EMULATOR_HOST"):
        initialize_app(options={
            'projectId': TEST_SETTINGS["PROJECT_ID"],
        })