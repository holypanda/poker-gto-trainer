from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base


class TrainingSession(Base):
    __tablename__ = "training_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 训练配置
    stack_size = Column(Integer, nullable=False)  # 50 or 100
    position = Column(String, nullable=False)  # BTN, CO, MP, UTG, SB, BB
    action_to_you = Column(String, nullable=False)  # fold, limp, raise_2bb, raise_2.5bb, raise_3bb, all_in, etc.
    
    # 训练数据 (JSON array of scenarios)
    scenarios = Column(JSON, nullable=False)
    
    # 训练状态
    current_index = Column(Integer, default=0)
    correct_count = Column(Integer, default=0)
    completed = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    user = relationship("User", back_populates="training_sessions")
    records = relationship("TrainingRecord", back_populates="session", cascade="all, delete-orphan")
