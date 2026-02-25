from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.db.base import get_db
from app.core.config import settings
from app.core.security import create_access_token, verify_password
from app.schemas.user import UserCreate, User, UserStats
from app.services.user_service import (
    create_user, get_user_by_email, get_user_by_username,
    authenticate_user, get_user_stats
)
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
def register(user_create: UserCreate, db: Session = Depends(get_db)):
    """用户注册"""
    # 检查邮箱是否已存在
    if get_user_by_email(db, user_create.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # 检查用户名是否已存在
    if get_user_by_username(db, user_create.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # 创建用户
    user = create_user(db, user_create)
    return user


@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """用户登录"""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "username": user.username},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "is_subscribed": user.is_subscribed
        }
    }


@router.get("/me", response_model=User)
def get_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """获取当前用户信息"""
    return current_user


@router.get("/stats", response_model=UserStats)
def get_my_stats(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """获取当前用户统计"""
    stats = get_user_stats(db, current_user)
    return UserStats(**stats)
