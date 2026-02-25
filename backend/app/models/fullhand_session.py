"""
完整牌局模拟会话模型
V1.1 新增
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, JSON, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base


class FullHandSession(Base):
    """完整牌局会话"""
    __tablename__ = "fullhand_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # 配置
    table_type = Column(String, default="6max")
    stack_bb = Column(Integer, default=100)
    ai_level = Column(String, default="standard")
    
    # 随机种子 (用于重打)
    hand_seed = Column(String, nullable=False)
    
    # 牌局状态
    status = Column(String, default="INIT")  # INIT, PREFLOP, FLOP_DECISION, FAST_FORWARD, ENDED
    current_street = Column(String, default="preflop")  # preflop, flop, turn, river
    
    # 牌局数据 (JSON)
    players = Column(JSON, default=list)  # List[PlayerState]
    button_seat = Column(Integer, default=0)
    sb_seat = Column(Integer, default=1)
    bb_seat = Column(Integer, default=2)
    pot = Column(Float, default=0.0)
    current_bet = Column(Float, default=0.0)
    community_cards = Column(JSON, default=list)  # List[str]
    action_log = Column(JSON, default=list)  # List[ActionRecord]
    
    # Hero 相关
    hero_seat = Column(Integer, nullable=True)
    hero_cards = Column(JSON, default=list)  # List[str]
    
    # 关键点记录 (JSON)
    preflop_key_spot = Column(JSON, nullable=True)
    flop_key_spot = Column(JSON, nullable=True)
    
    # 结果
    result_bb = Column(Float, nullable=True)  # +/- bb
    ended_by = Column(String, nullable=True)  # fold, showdown, allin, hero_fold_preflop
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关联
    user = relationship("User", back_populates="fullhand_sessions")


class FullHandStats(Base):
    """完整牌局统计（每日汇总）"""
    __tablename__ = "fullhand_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)  # 日期，无时区
    
    # 统计
    total_hands = Column(Integer, default=0)
    preflop_key_spots = Column(Integer, default=0)
    flop_key_spots = Column(Integer, default=0)
    
    # 正确率
    preflop_correct = Column(Integer, default=0)
    preflop_total = Column(Integer, default=0)
    flop_correct = Column(Integer, default=0)
    flop_total = Column(Integer, default=0)
    
    # 结果
    total_result_bb = Column(Float, default=0.0)
    
    # 时长
    total_duration_ms = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 联合唯一约束
    __table_args__ = (
        # 每天每用户一条记录
        {'sqlite_autoincrement': True},
    )
