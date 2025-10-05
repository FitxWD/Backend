from firebase_admin import firestore
from firebase_utils import initialize_firebase

def cleanup_test_data():
    """Clean up all test user data"""
    initialize_firebase()
    db = firestore.client()
    
    # Delete test user documents
    docs = db.collection('users').where('is_test_user', '==', True).get()
    
    for doc in docs:
        print(f"Deleting test user: {doc.id}")
        doc.reference.delete()

if __name__ == "__main__":
    cleanup_test_data()