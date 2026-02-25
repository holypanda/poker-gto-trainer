from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime


class PositionConfig(BaseModel):
    stack_size: int  # 50 or 100
    position: str  # BTN, CO, MP, UTG, SB, BB
    action_to_you: str  # fold, limp, raise_2bb, raise_2.5bb, etc.


class TrainingSessionCreate(PositionConfig):
    scenario_count: int = 10


class TrainingScenario(BaseModel):
    id: int
    hand: str  # e.g., "AKs", "72o"
    position: str
    vs_position: Optional[str] = None
    action_to_you: str
    options: List[str]  # 可用选项（已随机打乱）
    difficulty: Optional[str] = None  # easy, normal, hard
    time_limit: Optional[int] = None  # 答题时间限制（秒）


class GTOAction(BaseModel):
    action: str
    frequency: float  # 0-1


class ScenarioAnswer(BaseModel):
    scenario_id: int
    correct_action: str
    gto_frequency: Dict[str, float]  # action -> frequency
    explanation: Optional[str] = None


class TrainingAnswer(BaseModel):
    scenario_id: int
    action: str
    response_time_ms: Optional[int] = None


class TrainingResult(BaseModel):
    is_correct: bool
    correct_action: str
    user_action: str
    gto_frequency: Dict[str, float]
    explanation: Optional[str] = None
    score: int = 0  # 本题得分
    time_bonus: bool = False  # 是否有速度奖励


class TrainingRecordItem(BaseModel):
    hand: str
    position: str
    vs_position: Optional[str]
    action_to_you: str
    user_action: str
    correct_action: str
    is_correct: bool
    response_time_ms: Optional[int]


class TrainingSessionResponse(BaseModel):
    id: int
    stack_size: int
    position: str
    action_to_you: str
    scenarios: List[TrainingScenario]
    current_index: int
    completed: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class TrainingCompleteResponse(BaseModel):
    session_id: int
    total_scenarios: int
    correct_count: int
    accuracy: float
    records: List[TrainingRecordItem]


class HandAdvice(BaseModel):
    hand: str
    position: str
    vs_position: Optional[str]
    action_to_you: str
    stack_size: int
    advice: str
    gto_frequency: Dict[str, float]
    explanation: str


class DailyStats(BaseModel):
    date: str
    train_count: int
    correct_count: int
    accuracy: float


class OverallStats(BaseModel):
    total_trains: int
    correct_trains: int
    accuracy: float
    streak_days: int
    daily_stats: List[DailyStats]
    position_stats: Dict[str, Dict[str, int]]  # position -> {total, correct}
    hand_type_stats: Dict[str, Dict[str, int]]  # hand_type -> {total, correct}
