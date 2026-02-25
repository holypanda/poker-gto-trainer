from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.base import get_db
from app.models.user import User
from app.api.deps import get_current_user
from app.schemas.training import (
    TrainingSessionCreate, TrainingSessionResponse, TrainingAnswer,
    TrainingResult, TrainingCompleteResponse, OverallStats, HandAdvice
)
from app.services.training_service import (
    create_training_session, get_training_session, submit_answer,
    complete_training_session, get_user_training_history, get_overall_stats,
    get_hand_advice
)
from app.services.user_service import can_train, consume_train_credit, record_training_result

router = APIRouter(prefix="/training", tags=["训练"])


@router.post("/sessions", response_model=TrainingSessionResponse)
def start_training(
    config: TrainingSessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """开始新的训练会话"""
    
    # 检查是否可以训练
    if not can_train(db, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Daily free training limit reached. Please subscribe to continue."
        )
    
    # 消耗训练次数
    consume_train_credit(db, current_user)
    
    # 创建训练会话
    session = create_training_session(db, current_user, config)
    
    return TrainingSessionResponse(
        id=session.id,
        stack_size=session.stack_size,
        position=session.position,
        action_to_you=session.action_to_you,
        scenarios=session.scenarios,
        current_index=session.current_index,
        completed=session.completed,
        created_at=session.created_at
    )


@router.get("/sessions/{session_id}", response_model=TrainingSessionResponse)
def get_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取训练会话详情"""
    session = get_training_session(db, session_id, current_user.id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Training session not found"
        )
    
    return TrainingSessionResponse(
        id=session.id,
        stack_size=session.stack_size,
        position=session.position,
        action_to_you=session.action_to_you,
        scenarios=session.scenarios,
        current_index=session.current_index,
        completed=session.completed,
        created_at=session.created_at
    )


@router.post("/sessions/{session_id}/answer", response_model=TrainingResult)
def submit_training_answer(
    session_id: int,
    answer: TrainingAnswer,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """提交训练答案"""
    session = get_training_session(db, session_id, current_user.id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Training session not found"
        )
    
    if session.completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Training session already completed"
        )
    
    # 提交答案
    result = submit_answer(db, session, answer)
    
    # 更新用户统计
    record_training_result(db, current_user, result.is_correct)
    
    return result


@router.post("/sessions/{session_id}/complete", response_model=TrainingCompleteResponse)
def complete_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """完成训练会话"""
    session = get_training_session(db, session_id, current_user.id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Training session not found"
        )
    
    return complete_training_session(db, session)


@router.get("/history", response_model=List[TrainingSessionResponse])
def get_history(
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取训练历史"""
    # 验证分页参数
    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="limit must be between 1 and 100"
        )
    if offset < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="offset must be non-negative"
        )
    
    sessions = get_user_training_history(db, current_user.id, limit, offset)
    
    return [
        TrainingSessionResponse(
            id=s.id,
            stack_size=s.stack_size,
            position=s.position,
            action_to_you=s.action_to_you,
            scenarios=s.scenarios,
            current_index=s.current_index,
            completed=s.completed,
            created_at=s.created_at
        )
        for s in sessions
    ]


@router.get("/stats", response_model=OverallStats)
def get_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取训练统计"""
    return get_overall_stats(db, current_user.id)


@router.get("/advice", response_model=HandAdvice)
def get_advice(
    hand: str,
    position: str,
    action_to_you: str,
    stack_size: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取手牌建议"""
    advice = get_hand_advice(db, hand, position, action_to_you, stack_size)
    
    return HandAdvice(
        hand=hand,
        position=position,
        vs_position=None,
        action_to_you=action_to_you,
        stack_size=stack_size,
        advice=advice['best_action'],
        gto_frequency=advice['strategy'],
        explanation=advice['explanation']
    )
