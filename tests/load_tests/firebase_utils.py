from firebase_admin import credentials, initialize_app, auth, _apps
from dotenv import load_dotenv
import os
import requests

# Load environment variables
load_dotenv()

# Get API key
FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY")
if not FIREBASE_API_KEY:
    raise ValueError("FIREBASE_API_KEY not found in environment variables")

def initialize_firebase():
    """Initialize Firebase Admin"""
    try:
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        service_account_path = os.path.join(root_dir, 'serviceAccountKey.json')
        
        if not os.path.exists(service_account_path):
            raise FileNotFoundError(f"Service account file not found at: {service_account_path}")
            
        print(f"✅ Loading Firebase credentials from: {service_account_path}")
        cred = credentials.Certificate(service_account_path)
        
        # Check if Firebase is already initialized
        if not _apps:
            initialize_app(cred)
            print("✅ Firebase Admin SDK initialized successfully")
        else:
            print("✅ Firebase Admin SDK already initialized")
        
        return True
        
    except Exception as e:
        print(f"❌ Firebase initialization error: {str(e)}")
        raise

def create_test_user():
    """Create a test user and get ID token"""
    try:
        # Create random email for test user
        email = f"test_{os.urandom(4).hex()}@test.com"
        password = "Test123!"
        
        # Create user in Firebase Auth
        user = auth.create_user(
            email=email,
            password=password,
            email_verified=True
        )

        # Get custom token
        custom_token = auth.create_custom_token(user.uid)

        # Exchange custom token for ID token using REST API
        response = requests.post(
            f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken",
            params={"key": FIREBASE_API_KEY},
            json={
                "token": custom_token.decode(),
                "returnSecureToken": True
            }
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to get ID token: {response.text}")
            
        id_token = response.json()["idToken"]
        print(f"✅ Created test user {user.uid} with ID token")
        return user.uid, id_token

    except Exception as e:
        print(f"❌ Error creating test user: {str(e)}")
        return None, None

def delete_test_user(uid):
    """Delete a test user"""
    try:
        auth.delete_user(uid)
        print(f"✅ Deleted test user: {uid}")
    except Exception as e:
        print(f"❌ Error deleting test user: {str(e)}")