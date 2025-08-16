from app.repositories.user_repository import UserRepository
from typing import List, Dict, Any

class UserService:
    def __init__(self):
        self.user_repository = UserRepository()
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        return self.user_repository.get_all()
    
    def get_user_by_id(self, user_id: int) -> Dict[str, Any] | None:
        return self.user_repository.get_by_id(user_id)

# For backward compatibility, keep the function
def get_all_users():
    service = UserService()
    return service.get_all_users()