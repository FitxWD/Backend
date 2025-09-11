from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from app.deps.auth import verify_firebase_token
from app.config import db
from app.api.v1.schemas.user import ProfileUpdate

router = APIRouter()

@router.get("/me")
def me(user=Depends(verify_firebase_token)) -> Dict[str, Any]:
    # user is decoded token; user["uid"] is the Firebase UID
    return {"uid": user["uid"], "email": user.get("email")}

@router.get("/profile")
def get_profile(user=Depends(verify_firebase_token)):
    uid = user["uid"]
    doc_ref = db.collection("users").document(uid).get()
    if doc_ref.exists:
        return doc_ref.to_dict()
    return {}

@router.post("/profile-health-update")
def upsert_profile(profile: ProfileUpdate, user=Depends(verify_firebase_token)):
    uid = user["uid"]
    profile_data = profile.dict(exclude_none=True)
    db.collection("users").document(uid).set(profile_data, merge=True)
    return {"ok": True}