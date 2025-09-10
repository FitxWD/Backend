from pydantic import BaseModel, Field
from typing import List, Optional, Union
from enum import Enum
from datetime import datetime

# --- Enums ---
class Role(str, Enum):
    user = "user"
    admin = "admin"

class WorkoutType(str, Enum):
    strength = "strength"
    cardio = "cardio"
    flexibility = "flexibility"
    mixed = "mixed"

class Level(str, Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"


# --- User Models ---
class HealthData(BaseModel):
    gender: str
    age: int = Field(..., gt=0, lt=120)
    weight: float = Field(..., gt=0, description="Weight in kg")
    height: float = Field(..., gt=50, lt=300, description="Height in cm")

class User(BaseModel):
    id: Optional[str] = None
    email: str
    username: str
    role: Role = Role.user
    preferences: Optional[List[str]] = []
    healthData: HealthData


# --- Workout Models ---
class Exercise(BaseModel):
    name: str
    sets: int = Field(..., gt=0)
    reps: Union[int, str]  # can be a number or "max"
    durationSeconds: Optional[int] = Field(None, gt=0)

class WorkoutTemplate(BaseModel):
    id: Optional[str] = None
    name: str
    description: str
    type: WorkoutType
    level: Level
    durationMinutes: int = Field(..., gt=0)
    exercises: List[Exercise]


# --- Diet Models ---
class Meal(BaseModel):
    name: str
    description: str
    calories: int = Field(..., gt=0)

class CalorieRange(BaseModel):
    min: int = Field(..., gt=0)
    max: int = Field(..., gt=0)

class DietTemplate(BaseModel):
    id: Optional[str] = None
    name: str
    description: str
    calorieRange: CalorieRange
    tags: List[str]
    meals: List[Meal]


# --- Feedback Models ---
class Feedback(BaseModel):
    id: Optional[str] = None
    userId: str
    planId: Optional[str] = None
    message: str
    submittedAt: datetime
    status: str = "new"

class ProfileUpdate(BaseModel):
    gender: Optional[str] = Field(None, description="User gender")
    age: Optional[int] = Field(None, gt=0, lt=120, description="Age in years")
    weight: Optional[float] = Field(None, gt=0, description="Weight in kg")
    height: Optional[float] = Field(None, gt=50, lt=300, description="Height in cm")

class Config:
        # Ensures datetime is serialized as ISO 8601 string
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }