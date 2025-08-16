from fastapi import APIRouter, HTTPException
from app.services.user_service import UserService
from typing import List, Dict, Any

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