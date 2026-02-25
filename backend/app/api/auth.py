from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
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

# 创建速率限制器
limiter = Limiter(key_func=get_remote_address)


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
def register(request: Request, user_create: UserCreate, db: Session = Depends(get_db)):
    """用户注册 - 限制每分钟5次"""
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
@limiter.limit("10/minute")
def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """用户登录 - 限制每分钟10次"""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 检查用户是否活跃
    if hasattr(user, 'is_active') and not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "username": user.username},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
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
