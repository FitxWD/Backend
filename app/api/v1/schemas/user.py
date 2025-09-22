from pydantic import BaseModel, Field
from typing import List, Optional, Union, Dict, Any
from enum import Enum
from datetime import datetime

# # --- Enums ---
# class Role(str, Enum):
#     user = "user"
#     admin = "admin"

# class WorkoutType(str, Enum):
#     strength = "strength"
#     cardio = "cardio"
#     flexibility = "flexibility"
#     mixed = "mixed"

# class Level(str, Enum):
#     beginner = "beginner"
#     intermediate = "intermediate"
#     advanced = "advanced"


# # --- User Models ---
# class HealthData(BaseModel):
#     gender: str
#     age: int = Field(..., gt=0, lt=120)
#     weight: float = Field(..., gt=0, description="Weight in kg")
#     height: float = Field(..., gt=50, lt=300, description="Height in cm")

# class User(BaseModel):
#     id: Optional[str] = None
#     email: str
#     username: str
#     role: Role = Role.user
#     preferences: Optional[List[str]] = []
#     healthData: HealthData


# # --- Workout Models ---
# class Exercise(BaseModel):
#     name: str
#     sets: int = Field(..., gt=0)
#     reps: Union[int, str]  # can be a number or "max"
#     durationSeconds: Optional[int] = Field(None, gt=0)

# class WorkoutTemplate(BaseModel):
#     id: Optional[str] = None
#     name: str
#     description: str
#     type: WorkoutType
#     level: Level
#     durationMinutes: int = Field(..., gt=0)
#     exercises: List[Exercise]


# # --- Diet Models ---
# class Meal(BaseModel):
#     name: str
#     description: str
#     calories: int = Field(..., gt=0)

# class CalorieRange(BaseModel):
#     min: int = Field(..., gt=0)
#     max: int = Field(..., gt=0)

# class DietTemplate(BaseModel):
#     id: Optional[str] = None
#     name: str
#     description: str
#     calorieRange: CalorieRange
#     tags: List[str]
#     meals: List[Meal]


# # --- Feedback Models ---
# class Feedback(BaseModel):
#     id: Optional[str] = None
#     userId: str
#     planId: Optional[str] = None
#     message: str
#     submittedAt: datetime
#     status: str = "new"
    
class HealthData(BaseModel):
    gender: Optional[str] = Field(None, description="User gender")
    age: Optional[int] = Field(None, gt=0, lt=120, description="Age in years")
    weight: Optional[float] = Field(None, gt=0, description="Weight in kg")
    height: Optional[float] = Field(None, gt=50, lt=300, description="Height in cm")

class ProfileUpdate(BaseModel):
    healthData: HealthData

# All fields that aren't 'name' are optional
class Exercise(BaseModel):
    name: str
    duration_min: Optional[int] = None
    sets: Optional[int] = None
    reps: Optional[str] = None
    example: Optional[str] = None

# The Session model now makes entire sections optional
class Session(BaseModel):
    warmup: Optional[List[Exercise]] = None  #optional
    main: List[Exercise]
    cooldown: Optional[List[Exercise]] = None #optional
    safety: Optional[List[str]] = None       #optional

class DailyTemplate(BaseModel):
    day: str
    sessions: List[Session]

class MicroWorkout(BaseModel):
    name: str
    duration_min: int
    example: Optional[str] = None
    drills: Optional[List[str]] = None

class WorkoutPlan(BaseModel):
    name: str
    description: str
    goals: List[str]
    level: str
    durationMinutes: Optional[int] = None
    weekly_template: List[DailyTemplate]
    micro_workouts: List[MicroWorkout]
    progression_4_weeks: List[str]
    personalization_rules: List[str]

class MacroTargets(BaseModel):
    carbs_g: int
    protein_g: int
    fat_g: int

class AlternativeMeal(BaseModel):
    name: str
    approx_kcal: int

class Meal(BaseModel):
    name: str
    description: str
    ingredients: List[str]
    approx_kcal: int
    alternatives: List[AlternativeMeal]

class DailyDiet(BaseModel):
    day: int
    meals: List[Meal]

class DietPlan(BaseModel):
    id: str
    diet_type: str
    calorie_range: str
    macro_targets: MacroTargets
    sodium_target_mg: int
    notes: str
    days: List[DailyDiet]

class Config:
        # Ensures datetime is serialized as ISO 8601 string
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }