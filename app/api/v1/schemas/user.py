from pydantic import BaseModel, Field, constr
from typing import List, Optional, Union, Dict, Any
from enum import Enum
from datetime import datetime

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
    lastEdited: datetime

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

class PlanAcceptanceRequest(BaseModel):
    plan_id: str
    plan_type: str
    user_id: str
    accepted: bool

class FeedbackPayload(BaseModel):
    planId: str
    rating: int = Field(..., ge=1, le=5, description="Rating must be an integer between 1 and 5")
    text: Optional[str] = Field(..., min_length=1, max_length=2000, description="Text must not be empty")

class FeedbackStatus(str, Enum):
    new = "new"
    reviewed = "reviewed" # Changed from "revised" for clarity

class UpdateStatusPayload(BaseModel):
    status: FeedbackStatus

class UserInfo(BaseModel):
    uid: str
    email: Optional[str] = None
    displayName: Optional[str] = None

class FeedbackResponse(BaseModel):
    id: str  # The document ID
    user: UserInfo
    planId: str
    rating: int
    text: str
    createdAt: str
    status: FeedbackStatus

class FeedbackCountStats(BaseModel):
    new: int
    reviewed: int
    total: int

class RecentFeedback(BaseModel):
    id: str
    text: str
    rating: int
    userEmail: str

class RecentUser(BaseModel):
    uid: str
    email: str
    createdAt: datetime

class DailyGrowth(BaseModel):
    date: str
    count: int

class RecentPlan(BaseModel):
    id: str
    name: str
    type: str # 'diet' or 'workout'
    lastEdited: datetime

class DashboardStats(BaseModel):
    totalUsers: int
    newUsersToday: int
    feedbackCounts: FeedbackCountStats
    totalWorkoutPlans: int
    totalDietPlans: int
    workoutPlansEditedToday: int  
    dietPlansEditedToday: int    
    recentlyEditedPlans: List[RecentPlan]
    recentFeedbacks: List[RecentFeedback]
    recentUsers: List[RecentUser]
    userGrowthLast7Days: List[DailyGrowth]

class DietPlanUpdate(BaseModel):
    macro_targets: MacroTargets
    notes: str
    days: List[DailyDiet]