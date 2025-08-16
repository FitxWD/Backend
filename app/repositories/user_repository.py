from typing import List, Dict, Any

class UserRepository:
    def __init__(self):
        # In a real app, this would connect to a database
        self._users = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"}
        ]
    
    def get_all(self) -> List[Dict[str, Any]]:
        return self._users
    
    def get_by_id(self, user_id: int) -> Dict[str, Any] | None:
        return next((user for user in self._users if user["id"] == user_id), None)