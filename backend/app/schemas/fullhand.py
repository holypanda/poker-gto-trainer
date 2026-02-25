"""
完整牌局模拟的 Pydantic Schemas
V1.1 新增
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime


# ========== 基础数据结构 ==========

class PlayerState(BaseModel):
    """玩家状态"""
    seat: int
    position: str  # UTG, MP, CO, BTN, SB, BB
    stack: float
    in_hand: bool
    committed_this_street: float
    total_committed: float
    hole_cards: Optional[List[str]] = None  # 仅 Hero 可见
    is_hero: bool
    is_active: bool  # 本轮是否还能行动


class ActionRecord(BaseModel):
    """行动记录"""
    street: str
    seat: int
    position: str
    action: str  # fold, check, call, bet, raise, allin, sb, bb, deal
    amount: Optional[float] = None
    pot_after: float
    timestamp: Optional[str] = None


class KeySpotInfo(BaseModel):
    """关键点信息"""
    street: str
    context_id: str
    pot_type: Optional[str] = None  # SRP, 3BP, 4BP
    ip_oop: Optional[str] = None  # IP, OOP
    spr_bucket: Optional[str] = None  # LOW, MED, HIGH
    board: Optional[List[str]] = None
    hero_hand: str
    hero_hand_bucket: Optional[str] = None
    legal_actions: List[str]
    strategy: Optional[Dict[str, float]] = None  # Pro 才展示完整
    best_action: str


# ========== 请求 Schemas ==========

class FullHandStartRequest(BaseModel):
    """开始一局请求"""
    table_type: str = "6max"
    stack_bb: int = 100
    ai_level: str = "standard"
    replay_seed: Optional[str] = None  # Pro 重打时使用


class FullHandActRequest(BaseModel):
    """执行动作请求"""
    hand_id: int
    action: str  # fold, check, call, bet, raise, allin
    amount: Optional[float] = None  # bet/raise 时需要


class FullHandReplayRequest(BaseModel):
    """重打请求"""
    hand_id: int


# ========== 响应 Schemas ==========

class GameState(BaseModel):
    """游戏状态"""
    status: str
    street: str
    players: List[PlayerState]
    button_seat: int
    sb_seat: int
    bb_seat: int
    pot: float
    current_bet: float
    community_cards: List[str]
    to_act_seat: Optional[int] = None
    hero_seat: int
    hero_cards: List[str]
    min_raise_to: Optional[float] = None


class FullHandStartResponse(BaseModel):
    """开始一局响应"""
    hand_id: int
    state: GameState
    legal_actions: List[str]
    action_log: List[ActionRecord]
    is_key_spot: bool = False
    key_spot_info: Optional[KeySpotInfo] = None


class FullHandActResponse(BaseModel):
    """执行动作响应"""
    state: GameState
    legal_actions: List[str]
    is_key_spot: bool
    key_spot_info: Optional[KeySpotInfo] = None
    final_result: Optional[Dict[str, Any]] = None  # 如果游戏结束
    review_payload: Optional[Dict[str, Any]] = None  # 如果游戏结束


class PreflopSpotReview(BaseModel):
    """翻前关键点复盘"""
    context_id: str
    strategy: Optional[Dict[str, float]] = None  # Free 裁剪
    user_action: str
    user_action_prob: Optional[float] = None  # Free 裁剪
    best_action: str
    grade: str  # PERFECT, ACCEPTABLE, WRONG


class FlopSpotReview(BaseModel):
    """翻牌关键点复盘"""
    context_id: str
    pot_type: str
    ip_oop: str
    spr_bucket: str
    board: List[str]
    hero_hand: str
    hero_hand_bucket: str
    strategy: Optional[Dict[str, float]] = None  # Free 裁剪
    legal_actions: List[str]
    user_action: str
    user_action_prob: Optional[float] = None  # Free 裁剪
    best_action: str
    grade: str
    explanation: str


class PlayerShowdownResult(BaseModel):
    """玩家摊牌结果"""
    seat: int
    position: str
    hole_cards: List[str]
    is_hero: bool
    in_hand: bool
    total_committed: float
    score: int
    hand_name: str
    is_winner: bool


class ShowdownAnalysis(BaseModel):
    """摊牌详细分析"""
    community_cards: List[str]
    pot: float
    players: List[PlayerShowdownResult]
    winner_analysis: Optional[Dict[str, Any]] = None
    explanation: str


class FullHandReviewResponse(BaseModel):
    """复盘响应"""
    hand_id: int
    result_bb: float
    ended_by: str
    action_log: List[ActionRecord]
    preflop_spot: Optional[PreflopSpotReview] = None
    flop_spot: Optional[FlopSpotReview] = None
    can_replay: bool  # 是否支持重打 (Pro)
    showdown_analysis: Optional[ShowdownAnalysis] = None  # 摊牌详细分析


class FullHandHistoryItem(BaseModel):
    """历史记录项"""
    hand_id: int
    stack_bb: int
    result_bb: float
    ended_by: str
    has_flop_spot: bool
    flop_grade: Optional[str] = None
    created_at: datetime


class FullHandStatsResponse(BaseModel):
    """统计响应"""
    total_hands: int
    total_result_bb: float
    avg_result_bb: float
    preflop_accuracy: Optional[float] = None
    flop_accuracy: Optional[float] = None
    today_hands: int
    today_remaining: int  # Free 用户今日剩余局数
    is_pro: bool
