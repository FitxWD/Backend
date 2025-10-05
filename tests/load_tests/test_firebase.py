from firebase_utils import initialize_firebase

def test_firebase_setup():
    print("\n🔍 Testing Firebase Setup")
    print("-" * 50)
    try:
        initialize_firebase()
        print("✅ Firebase setup verified successfully!")
    except Exception as e:
        print(f"❌ Setup failed: {str(e)}")

if __name__ == "__main__":
    test_firebase_setup()