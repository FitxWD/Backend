from firebase_utils import initialize_firebase, create_test_user, delete_test_user
import requests
import json

def test_auth_flow():
    """Test the complete user flow: signup -> profile update -> profile fetch"""
    print("\n🔍 Testing Authentication Flow")
    print("-" * 50)
    
    # Initialize Firebase
    initialize_firebase()
    
    # Create test user
    uid, token = create_test_user()
    if not uid or not token:
        print("❌ Failed to create test user")
        return
    
    print(f"\n✅ Created test user: {uid}")
    print(f"Token preview: {token[:50]}...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # First create a profile (matching frontend data structure)
    try:
        profile_data = {
            "healthData": {
                "gender": "male",  # Frontend sends lowercase
                "age": 25,
                "weight": 70.0,
                "height": 175.0
            },
            "is_test_user": True
        }
        
        print("\n📝 Creating health profile...")
        create_response = requests.post(
            "http://localhost:8000/api/v1/profile-health-update",
            headers=headers,
            json=profile_data
        )
        print(f"Create Profile Status: {create_response.status_code}")
        if create_response.status_code == 200:
            print("✅ Profile created successfully")
        else:
            print(f"❌ Profile creation failed: {create_response.text}")
        
        # Then fetch the profile
        print("\n🔍 Fetching profile...")
        get_response = requests.get(
            "http://localhost:8000/api/v1/profile",
            headers=headers
        )
        print(f"Get Profile Status: {get_response.status_code}")
        
        if get_response.status_code == 200:
            profile = get_response.json()
            print("\n📊 Retrieved Profile Data:")
            print(json.dumps(profile, indent=2))
            
            # Verify profile data matches what we sent
            health_data = profile.get("healthData", {})
            if all(
                health_data.get(k) == profile_data["healthData"][k] 
                for k in ["gender", "age", "weight", "height"]
            ):
                print("✅ Profile data verified successfully")
            else:
                print("❌ Profile data verification failed")
                print("Expected:", profile_data["healthData"])
                print("Got:", health_data)
        else:
            print(f"❌ Profile fetch failed: {get_response.text}")
        
    except Exception as e:
        print(f"❌ API call failed: {str(e)}")
    finally:
        # Cleanup
        print("\n🧹 Cleaning up test data...")
        delete_test_user(uid)
        print("✅ Test completed")

if __name__ == "__main__":
    test_auth_flow()