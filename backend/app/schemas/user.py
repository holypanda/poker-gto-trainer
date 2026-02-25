from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    username: str


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: Optional[str] = None


class UserStats(BaseModel):
    total_trains: int
    correct_trains: int
    accuracy: float
    streak_days: int
    is_subscribed: bool
    subscription_expires_at: Optional[datetime] = None
    free_trains_today: int
    free_trains_reset_at: Optional[datetime] = None


class User(UserBase):
    id: int
    total_trains: int
    correct_trains: int
    accuracy: float
    streak_days: int
    is_subscribed: bool
    subscription_expires_at: Optional[datetime] = None
    free_trains_today: int
    free_trains_reset_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserInToken(BaseModel):
    id: int
    email: str
    username: str
