import firebase_admin
from firebase_admin import credentials, firestore
import os
import hashlib
from typing import Optional, Dict, Any

# Initialize Firebase for testing
if not firebase_admin._apps:
    # Use emulator for testing
    os.environ["FIRESTORE_EMULATOR_HOST"] = "localhost:8080"
    firebase_admin.initialize_app()

# Get Firestore client
db = firestore.client()

def add_user(user_id: str, user_data: dict):
    """Add a user to Firestore"""
    try:
        db.collection('users').document(user_id).set(user_data)
        return True
    except Exception as e:
        print(f"Error adding user: {e}")
        return False

def get_user(user_id: str):
    """Get a user from Firestore"""
    try:
        doc = db.collection('users').document(user_id).get()
        if doc.exists:
            return doc.to_dict()
        return None
    except Exception as e:
        print(f"Error getting user: {e}")
        return None

def update_user(user_id: str, user_data: dict):
    """Update a user in Firestore"""
    try:
        db.collection('users').document(user_id).update(user_data)
        return True
    except Exception as e:
        print(f"Error updating user: {e}")
        return False

def delete_user(user_id: str):
    """Delete a user from Firestore"""
    try:
        db.collection('users').document(user_id).delete()
        return True
    except Exception as e:
        print(f"Error deleting user: {e}")
        return False

def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get a user by email address"""
    try:
        users_ref = db.collection('users')
        query = users_ref.where('email', '==', email).limit(1)
        docs = query.get()
        
        if docs:
            for doc in docs:
                user_data = doc.to_dict()
                user_data['user_id'] = doc.id  # Include document ID
                return user_data
        return None
    except Exception as e:
        print(f"Error getting user by email: {e}")
        return None

def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    """Authenticate a user with email and password"""
    try:
        # Get user by email
        user_data = get_user_by_email(email)
        
        if not user_data:
            print(f"No user found with email: {email}")
            return None
        
        # Check if account is active
        if not user_data.get('isActive', True):
            print(f"Account is deactivated for email: {email}")
            return None
        
        # In a real application, you would hash the password and compare
        # For now, we'll do a simple comparison (NOT SECURE - just for testing)
        stored_password = user_data.get('password')
        
        if stored_password == password:
            # Remove password from returned data for security
            user_data_safe = {k: v for k, v in user_data.items() if k != 'password'}
            return user_data_safe
        else:
            print(f"Invalid password for email: {email}")
            return None
            
    except Exception as e:
        print(f"Error authenticating user: {e}")
        return None

def hash_password(password: str) -> str:
    """Hash a password using SHA256 (in production, use bcrypt or similar)"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return hash_password(password) == hashed_password

def create_user_account(full_name: str, email: str, password: str) -> Optional[str]:
    """Create a new user account (registration flow)"""
    try:
        # Check if user already exists
        existing_user = get_user_by_email(email)
        if existing_user:
            print(f"User already exists with email: {email}")
            return None
        
        # Hash the password
        hashed_password = hash_password(password)
        
        # Create user data
        user_data = {
            "fullName": full_name,
            "email": email,
            "password": hashed_password,
            "role": "user",
            "profileComplete": False,
            "isActive": True,
            "createdAt": firestore.SERVER_TIMESTAMP
        }
        
        # Generate a user ID
        user_ref = db.collection('users').document()
        user_id = user_ref.id
        
        # Add user to database
        if add_user(user_id, user_data):
            return user_id
        return None
        
    except Exception as e:
        print(f"Error creating user account: {e}")
        return None

def complete_user_profile(user_id: str, health_data: dict) -> bool:
    """Complete user profile with health data"""
    try:
        update_data = {
            "healthData": health_data,
            "profileComplete": True,
            "profileCompletedAt": firestore.SERVER_TIMESTAMP
        }
        
        return update_user(user_id, update_data)
        
    except Exception as e:
        print(f"Error completing user profile: {e}")
        return False

def update_last_login(user_id: str) -> bool:
    """Update user's last login timestamp"""
    try:
        update_data = {
            "lastLoginAt": firestore.SERVER_TIMESTAMP,
            "isOnline": True
        }
        
        return update_user(user_id, update_data)
        
    except Exception as e:
        print(f"Error updating last login: {e}")
        return False

def validate_registration_data(full_name: str, email: str, password: str) -> tuple[bool, str]:
    """Validate registration form data"""
    # Check full name
    if not full_name or len(full_name.strip()) == 0:
        return False, "Full name is required"
    
    # Check email format
    if not email or "@" not in email or "." not in email.split("@")[-1]:
        return False, "Valid email address is required"
    
    # Check password strength
    if not password or len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"
    
    return True, "Valid"

def validate_health_data(gender: str, age: int, height: float, weight: float) -> tuple[bool, str]:
    """Validate health data from 'Tell Us About You' form"""
    # Check gender
    if gender not in ["Male", "Female", "Other"]:
        return False, "Gender must be Male, Female, or Other"
    
    # Check age
    if not (13 <= age <= 120):
        return False, "Age must be between 13 and 120 years"
    
    # Check height (cm)
    if not (100 <= height <= 250):
        return False, "Height must be between 100 and 250 cm"
    
    # Check weight (kg)
    if not (30 <= weight <= 300):
        return False, "Weight must be between 30 and 300 kg"
    
    return True, "Valid"

def calculate_bmi(height_cm: float, weight_kg: float) -> float:
    """Calculate BMI from height (cm) and weight (kg)"""
    height_m = height_cm / 100
    return weight_kg / (height_m ** 2)

def get_user_stats() -> dict:
    """Get database statistics (for admin/testing purposes)"""
    try:
        users_ref = db.collection('users')
        all_users = users_ref.get()
        
        total_users = len(all_users)
        complete_profiles = sum(1 for user in all_users if user.to_dict().get('profileComplete', False))
        active_users = sum(1 for user in all_users if user.to_dict().get('isActive', True))
        
        return {
            "total_users": total_users,
            "complete_profiles": complete_profiles,
            "incomplete_profiles": total_users - complete_profiles,
            "active_users": active_users,
            "inactive_users": total_users - active_users
        }
        
    except Exception as e:
        print(f"Error getting user stats: {e}")
        return {}

# Test function to check database connection
def test_connection():
    """Test the database connection"""
    try:
        # Try to read from the database
        test_doc = db.collection('test').document('connection_test').get()
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    # Test the connection when running this file directly
    test_connection()