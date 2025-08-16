from pydantic import BaseModel
from typing import List

class UserBase(BaseModel):
    name: str

class UserResponse(BaseModel):
    id: int
    name: str

class UsersListResponse(BaseModel):
    users: List[UserResponse]