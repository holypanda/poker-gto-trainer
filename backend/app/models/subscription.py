from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base
import json


class Subscription(Base):
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 支付宝信息
    alipay_trade_no = Column(String, nullable=True)
    alipay_buyer_id = Column(String, nullable=True)
    
    # 订阅信息
    amount = Column(Float, nullable=False)
    currency = Column(String, default="CNY")
    status = Column(String, default="pending")  # pending, active, cancelled, expired
    
    # 时间
    started_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # 元数据
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    user = relationship("User", back_populates="subscriptions")



