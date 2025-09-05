import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore, auth

# Load credentials from env
load_dotenv()

cred = credentials.Certificate(os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))

# Initialize only once
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

db = firestore.client()