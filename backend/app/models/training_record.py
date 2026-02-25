from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Float, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base


class TrainingRecord(Base):
    __tablename__ = "training_records"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("training_sessions.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 场景信息
    hand = Column(String, nullable=False)  # e.g., "AKs", "72o"
    position = Column(String, nullable=False)
    vs_position = Column(String, nullable=True)  # 对手位置（如有）
    action_to_you = Column(String, nullable=False)
    
    # 正确答案
    correct_action = Column(String, nullable=False)  # fold, call, raise_2.5bb, raise_3bb, all_in, etc.
    gto_frequency = Column(JSON, nullable=False)  # {action: frequency}
    
    # 用户答案
    user_action = Column(String, nullable=False)
    is_correct = Column(Boolean, nullable=False)
    
    # 时间
    response_time_ms = Column(Integer, nullable=True)  # 响应时间（毫秒）
    
    # 得分（新增）
    score = Column(Integer, default=0)  # 本题得分
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    session = relationship("TrainingSession", back_populates="records")
    user = relationship("User", back_populates="training_records")
