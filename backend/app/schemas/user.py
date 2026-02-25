import re
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    username: str


class UserCreate(UserBase):
    password: str
    
    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """验证密码强度"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v


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
