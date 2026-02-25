from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    
    # 统计
    total_trains = Column(Integer, default=0)
    correct_trains = Column(Integer, default=0)
    streak_days = Column(Integer, default=0)
    last_train_date = Column(DateTime, nullable=True)
    
    # 订阅状态
    is_subscribed = Column(Boolean, default=False)
    subscription_expires_at = Column(DateTime, nullable=True)
    
    # 免费额度
    free_trains_today = Column(Integer, default=20)
    free_trains_reset_at = Column(DateTime, nullable=True)
    
    # 元数据
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    training_sessions = relationship("TrainingSession", back_populates="user")
    training_records = relationship("TrainingRecord", back_populates="user")
    subscriptions = relationship("Subscription", back_populates="user")
    fullhand_sessions = relationship("FullHandSession", back_populates="user")
    
    @property
    def accuracy(self) -> float:
        if self.total_trains == 0:
            return 0.0
        return round(self.correct_trains / self.total_trains * 100, 1)
