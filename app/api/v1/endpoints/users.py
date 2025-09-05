from fastapi import APIRouter, Depends, HTTPException
from app.services.user_service import UserService
from typing import List, Dict, Any
from app.deps.auth import verify_firebase_token
from app.firebase import db

router = APIRouter()
user_service = UserService()

@router.get("/users")
def list_users() -> List[Dict[str, Any]]:
    """
    Fetch all users
    """
    return user_service.get_all_users()

@router.get("/users/{user_id}")
def get_user(user_id: int) -> Dict[str, Any]:
    """
    Fetch user by ID
    """
    user = user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/me")
def me(user=Depends(verify_firebase_token)) -> Dict[str, Any]:
    # user is decoded token; user["uid"] is the Firebase UID
    return {"uid": user["uid"], "email": user.get("email")}

@router.post("/profile")
def upsert_profile(profile: Dict[str, Any], user=Depends(verify_firebase_token)):
    uid = user["uid"]
    db.collection("users").document(uid).set(profile, merge=True)
    return {"ok": True}