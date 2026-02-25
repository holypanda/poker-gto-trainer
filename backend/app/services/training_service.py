from datetime import datetime
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.training_session import TrainingSession
from app.models.training_record import TrainingRecord
from app.models.user import User
from app.schemas.training import (
    TrainingSessionCreate, TrainingAnswer, TrainingResult,
    TrainingCompleteResponse, TrainingRecordItem, DailyStats, OverallStats
)
from app.services.gto_engine import generate_training_scenarios, get_gto_strategy
import random
import json


def _get_adaptive_difficulty(user: User) -> str:
    """
    根据用户历史表现动态调整难度
    """
    if user.total_trains < 10:
        return "normal"  # 新用户默认正常难度
    
    accuracy = user.accuracy
    
    if accuracy >= 80:
        return "hard"  # 正确率高，增加难度
    elif accuracy >= 60:
        return "normal"  # 正常水平
    else:
        return "easy"  # 正确率低，降低难度


def _calculate_score(is_correct: bool, response_time_ms: int, time_limit: int) -> int:
    """
    计算得分（考虑正确性和速度）
    """
    if not is_correct:
        return 0
    
    base_score = 100
    
    # 速度奖励
    if response_time_ms and time_limit:
        time_limit_ms = time_limit * 1000
        if response_time_ms < time_limit_ms * 0.5:
            base_score += 50  # 极快
        elif response_time_ms < time_limit_ms * 0.8:
            base_score += 20  # 较快
    
    return base_score


def create_training_session(
    db: Session, 
    user: User, 
    config: TrainingSessionCreate
) -> TrainingSession:
    """创建新的训练会话（增强版）"""
    
    # 根据用户历史正确率动态调整难度
    difficulty = _get_adaptive_difficulty(user)
    
    # 生成训练场景
    scenarios = generate_training_scenarios(
        stack_size=config.stack_size,
        position=config.position,
        action_to_you=config.action_to_you,
        count=config.scenario_count,
        difficulty=difficulty
    )
    
    session = TrainingSession(
        user_id=user.id,
        stack_size=config.stack_size,
        position=config.position,
        action_to_you=config.action_to_you,
        scenarios=scenarios,
        current_index=0,
        correct_count=0,
        completed=False
    )
    
    db.add(session)
    db.commit()
    db.refresh(session)
    
    return session


def get_training_session(db: Session, session_id: int, user_id: int) -> Optional[TrainingSession]:
    """获取训练会话"""
    return db.query(TrainingSession).filter(
        TrainingSession.id == session_id,
        TrainingSession.user_id == user_id
    ).first()


def submit_answer(
    db: Session,
    session: TrainingSession,
    answer: TrainingAnswer
) -> TrainingResult:
    """提交答案并返回结果（增强版）"""
    
    # 获取当前场景
    if session.current_index >= len(session.scenarios):
        raise ValueError("Training session already completed")
    
    scenario = session.scenarios[session.current_index]
    
    # 验证答案
    user_action = answer.action
    correct_action = scenario['correct_action']
    gto_frequency = scenario['gto_frequency']
    difficulty = scenario.get('difficulty', 'normal')
    time_limit = scenario.get('time_limit', 10)
    
    # 更严格的正确性判断
    user_freq = gto_frequency.get(user_action, 0)
    best_freq = gto_frequency.get(correct_action, 1.0)
    
    # 根据难度调整容差
    tolerance = {
        "easy": 0.25,    # 宽松
        "normal": 0.15,  # 正常
        "hard": 0.05     # 严格
    }.get(difficulty, 0.15)
    
    # 判断逻辑：
    # 1. 用户选择必须达到最低频率阈值
    # 2. 与最佳选择的频率差距不能太大
    is_correct = (user_freq >= tolerance and 
                  (best_freq - user_freq) <= tolerance * 2)
    
    # 特别处理：如果最佳选择频率很高(>0.7)，要求更严格
    if best_freq > 0.7 and user_action != correct_action:
        is_correct = False
    
    # 计算得分
    score = _calculate_score(is_correct, answer.response_time_ms, time_limit)
    
    # 创建训练记录
    record = TrainingRecord(
        session_id=session.id,
        user_id=session.user_id,
        hand=scenario['hand'],
        position=scenario['position'],
        vs_position=scenario.get('vs_position'),
        action_to_you=scenario['action_to_you'],
        correct_action=correct_action,
        gto_frequency=gto_frequency,
        user_action=user_action,
        is_correct=is_correct,
        response_time_ms=answer.response_time_ms,
        score=score
    )
    
    db.add(record)
    
    # 更新会话状态
    session.current_index += 1
    if is_correct:
        session.correct_count += 1
    
    # 检查是否完成
    if session.current_index >= len(session.scenarios):
        session.completed = True
        session.completed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(session)
    db.refresh(record)
    
    # 生成解释（根据用户选择给出个性化反馈）
    strategy = get_gto_strategy(session.stack_size)
    advice = strategy.get_advice(scenario['hand'], scenario['position'], scenario['action_to_you'])
    
    # 个性化解释
    explanation = _generate_personalized_explanation(
        advice['explanation'], is_correct, user_action, correct_action, 
        user_freq, best_freq, gto_frequency
    )
    
    return TrainingResult(
        is_correct=is_correct,
        correct_action=correct_action,
        user_action=user_action,
        gto_frequency=gto_frequency,
        explanation=explanation,
        score=score,
        time_bonus=score > 100
    )


def _generate_personalized_explanation(base_explanation: str, is_correct: bool, 
                                       user_action: str, correct_action: str,
                                       user_freq: float, best_freq: float,
                                       gto_frequency: dict) -> str:
    """生成个性化解释"""
    
    if is_correct:
        if user_action == correct_action:
            return f"✅ 完美！{base_explanation}"
        else:
            return f"✅ 可以接受。虽然最佳选择是 {correct_action}，但你的选择也有 {user_freq:.0%} 的 GTO 频率。"
    else:
        # 给出更具体的反馈
        if user_freq < 0.1:
            return f"❌ 偏离较大。{base_explanation} 你的选择在该情境下频率较低（{user_freq:.0%}）。"
        else:
            return f"⚠️ 接近但不完美。最佳选择是 {correct_action}（{best_freq:.0%}），你的选择是 {user_freq:.0%}。{base_explanation}"


def complete_training_session(
    db: Session,
    session: TrainingSession
) -> TrainingCompleteResponse:
    """完成训练会话并返回结果"""
    
    # 获取所有记录
    records = db.query(TrainingRecord).filter(
        TrainingRecord.session_id == session.id
    ).all()
    
    record_items = [
        TrainingRecordItem(
            hand=r.hand,
            position=r.position,
            vs_position=r.vs_position,
            action_to_you=r.action_to_you,
            user_action=r.user_action,
            correct_action=r.correct_action,
            is_correct=r.is_correct,
            response_time_ms=r.response_time_ms
        )
        for r in records
    ]
    
    total = len(records)
    correct = sum(1 for r in records if r.is_correct)
    accuracy = round(correct / total * 100, 1) if total > 0 else 0
    
    return TrainingCompleteResponse(
        session_id=session.id,
        total_scenarios=total,
        correct_count=correct,
        accuracy=accuracy,
        records=record_items
    )


def get_user_training_history(
    db: Session,
    user_id: int,
    limit: int = 20,
    offset: int = 0
) -> List[TrainingSession]:
    """获取用户训练历史"""
    return db.query(TrainingSession).filter(
        TrainingSession.user_id == user_id
    ).order_by(
        TrainingSession.created_at.desc()
    ).offset(offset).limit(limit).all()


def get_overall_stats(db: Session, user_id: int) -> OverallStats:
    """获取整体统计"""
    
    # 基础统计
    user = db.query(User).filter(User.id == user_id).first()
    
    # 每日统计 (最近30天)
    thirty_days_ago = datetime.utcnow() - __import__('datetime').timedelta(days=30)
    
    daily_records = db.query(
        func.date(TrainingRecord.created_at).label('date'),
        func.count().label('total'),
        func.sum(func.cast(TrainingRecord.is_correct, __import__('sqlalchemy').Integer)).label('correct')
    ).filter(
        TrainingRecord.user_id == user_id,
        TrainingRecord.created_at >= thirty_days_ago
    ).group_by(
        func.date(TrainingRecord.created_at)
    ).all()
    
    daily_stats = [
        DailyStats(
            date=str(r.date),
            train_count=r.total,
            correct_count=r.correct or 0,
            accuracy=round((r.correct or 0) / r.total * 100, 1) if r.total > 0 else 0
        )
        for r in daily_records
    ]
    
    # 位置统计
    position_records = db.query(
        TrainingRecord.position,
        func.count().label('total'),
        func.sum(func.cast(TrainingRecord.is_correct, __import__('sqlalchemy').Integer)).label('correct')
    ).filter(
        TrainingRecord.user_id == user_id
    ).group_by(
        TrainingRecord.position
    ).all()
    
    position_stats = {
        r.position: {'total': r.total, 'correct': r.correct or 0}
        for r in position_records
    }
    
    # 手牌类型统计
    records = db.query(TrainingRecord).filter(
        TrainingRecord.user_id == user_id
    ).all()
    
    from app.services.gto_engine import get_hand_type
    
    hand_type_data = {'pair': {'total': 0, 'correct': 0}, 
                      'suited': {'total': 0, 'correct': 0},
                      'offsuit': {'total': 0, 'correct': 0}}
    
    for r in records:
        ht = get_hand_type(r.hand)
        hand_type_data[ht]['total'] += 1
        if r.is_correct:
            hand_type_data[ht]['correct'] += 1
    
    return OverallStats(
        total_trains=user.total_trains,
        correct_trains=user.correct_trains,
        accuracy=user.accuracy,
        streak_days=user.streak_days,
        daily_stats=daily_stats,
        position_stats=position_stats,
        hand_type_stats=hand_type_data
    )


def get_hand_advice(
    db: Session,
    hand: str,
    position: str,
    action_to_you: str,
    stack_size: int
) -> Dict:
    """获取手牌建议"""
    strategy = get_gto_strategy(stack_size)
    return strategy.get_advice(hand, position, action_to_you)
