from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password
from app.core.config import settings


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def create_user(db: Session, user_create: UserCreate) -> User:
    hashed_password = get_password_hash(user_create.password)
    db_user = User(
        email=user_create.email,
        username=user_create.username,
        hashed_password=hashed_password,
        free_trains_reset_at=datetime.utcnow()
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 30


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """验证用户并处理账户锁定逻辑"""
    user = get_user_by_email(db, email)
    if not user:
        return None
    
    # 检查账户是否被锁定
    if user.locked_until and user.locked_until > datetime.utcnow():
        return None
    
    if not verify_password(password, user.hashed_password):
        # 登录失败，增加尝试次数
        user.login_attempts += 1
        
        # 超过最大尝试次数，锁定账户
        if user.login_attempts >= MAX_LOGIN_ATTEMPTS:
            user.locked_until = datetime.utcnow() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
            user.login_attempts = 0
        
        db.commit()
        return None
    
    # 登录成功，重置尝试次数
    if user.login_attempts > 0:
        user.login_attempts = 0
        user.locked_until = None
    
    # 更新最后登录时间
    user.last_login = datetime.utcnow()
    db.commit()
    
    return user


def update_user(db: Session, user: User, user_update: UserUpdate) -> User:
    update_data = user_update.model_dump(exclude_unset=True)
    
    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
    
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    return user


def check_and_reset_free_trains(db: Session, user: User) -> User:
    """检查并重置免费训练次数 (每天重置)"""
    now = datetime.utcnow()
    
    if user.free_trains_reset_at is None or user.free_trains_reset_at.date() < now.date():
        user.free_trains_today = settings.DEFAULT_DAILY_FREE_TRAINS
        user.free_trains_reset_at = now
        
        # 检查连续天数
        if user.last_train_date and (now.date() - user.last_train_date.date()).days == 1:
            user.streak_days += 1
        elif user.last_train_date and (now.date() - user.last_train_date.date()).days > 1:
            user.streak_days = 0
        
        db.commit()
        db.refresh(user)
    
    return user


def can_train(db: Session, user: User) -> bool:
    """检查用户是否可以进行训练"""
    user = check_and_reset_free_trains(db, user)
    
    # 订阅用户可以无限训练
    if user.is_subscribed and user.subscription_expires_at and user.subscription_expires_at > datetime.utcnow():
        return True
    
    # 免费用户检查次数
    return user.free_trains_today > 0


def consume_train_credit(db: Session, user: User) -> User:
    """消耗一次训练额度"""
    user = check_and_reset_free_trains(db, user)
    
    # 如果不是订阅用户，消耗免费次数
    if not (user.is_subscribed and user.subscription_expires_at and user.subscription_expires_at > datetime.utcnow()):
        if user.free_trains_today > 0:
            user.free_trains_today -= 1
    
    # 更新训练统计
    user.total_trains += 1
    user.last_train_date = datetime.utcnow()
    
    db.commit()
    db.refresh(user)
    return user


def record_training_result(db: Session, user: User, is_correct: bool) -> User:
    """记录训练结果"""
    if is_correct:
        user.correct_trains += 1
    
    db.commit()
    db.refresh(user)
    return user


def get_user_stats(db: Session, user: User) -> dict:
    """获取用户统计信息"""
    user = check_and_reset_free_trains(db, user)
    
    return {
        "total_trains": user.total_trains,
        "correct_trains": user.correct_trains,
        "accuracy": user.accuracy,
        "streak_days": user.streak_days,
        "is_subscribed": user.is_subscribed and user.subscription_expires_at and user.subscription_expires_at > datetime.utcnow(),
        "subscription_expires_at": user.subscription_expires_at,
        "free_trains_today": user.free_trains_today,
        "free_trains_reset_at": user.free_trains_reset_at
    }
