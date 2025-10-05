from dotenv import load_dotenv
import os

def verify_firebase_setup():
    """Verify Firebase environment variables"""
    print("\n🔍 Checking Firebase Configuration")
    print("-" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Check API key
    api_key = os.getenv("FIREBASE_API_KEY")
    if api_key:
        masked_key = f"{api_key[:8]}...{api_key[-4:]}"
        print(f"✅ Firebase API Key found: {masked_key}")
    else:
        print("❌ Firebase API Key not found!")
        
    print("\nEnvironment Variables:")
    print(f"Working Directory: {os.getcwd()}")
    print(f".env file exists: {os.path.exists('.env')}")

if __name__ == "__main__":
    verify_firebase_setup()