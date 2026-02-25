"""
完整牌局模拟 API
V1.1 新增
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.models.user import User
from app.api.deps import get_current_user
from app.schemas.fullhand import (
    FullHandStartRequest, FullHandStartResponse, FullHandActRequest, 
    FullHandActResponse, FullHandReviewResponse, GameState, PlayerState,
    ActionRecord, KeySpotInfo, FullHandStatsResponse
)
from app.services.fullhand_service import FullHandService

router = APIRouter(prefix="/fullhand", tags=["完整牌局模拟"])


@router.post("/start", response_model=FullHandStartResponse)
def start_fullhand(
    request: FullHandStartRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """开始一局完整牌局"""
    service = FullHandService(db)
    
    # 检查额度
    can_start, remaining = service.can_start_session(current_user)
    if not can_start:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Daily limit reached. Remaining: {remaining}"
        )
    
    try:
        session = service.create_session(
            current_user, 
            stack_bb=request.stack_bb,
            replay_seed=request.replay_seed
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    
    # 构建响应
    state = GameState(
        status=session.status,
        street=session.current_street,
        players=[PlayerState(**p) for p in session.players],
        button_seat=session.button_seat,
        sb_seat=session.sb_seat,
        bb_seat=session.bb_seat,
        pot=session.pot,
        current_bet=session.current_bet,
        community_cards=session.community_cards,
        to_act_seat=session.hero_seat,  # 简化
        hero_seat=session.hero_seat,
        hero_cards=session.hero_cards,
    )
    
    # 获取合法动作
    from app.services.fullhand_engine import FullHandEngine
    engine = FullHandEngine(stack_bb=session.stack_bb, seed=session.hand_seed)
    engine.initialize_game()
    # 重放行动恢复状态
    for action_dict in session.action_log:
        if action_dict["action"] not in ["sb", "bb"]:
            engine._to_act_seat = action_dict["seat"]
            try:
                engine.process_action(action_dict["action"], action_dict.get("amount"))
            except:
                pass
    
    legal_actions = engine.get_legal_actions()
    action_log = [ActionRecord(**a) for a in session.action_log]
    
    return FullHandStartResponse(
        hand_id=session.id,
        state=state,
        legal_actions=legal_actions,
        action_log=action_log,
        is_key_spot=False,
    )


@router.post("/act", response_model=FullHandActResponse)
def act_fullhand(
    request: FullHandActRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """执行动作"""
    service = FullHandService(db)
    
    try:
        result = service.process_hero_action(
            request.hand_id, 
            current_user, 
            request.action, 
            request.amount
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    
    state = GameState(**result["state"])
    key_spot_info = KeySpotInfo(**result["key_spot_info"]) if result.get("key_spot_info") else None
    
    return FullHandActResponse(
        state=state,
        legal_actions=result["legal_actions"],
        is_key_spot=result["is_key_spot"],
        key_spot_info=key_spot_info,
        final_result=result.get("final_result"),
        review_payload=result.get("review_payload"),
    )


@router.get("/review/{hand_id}", response_model=FullHandReviewResponse)
def get_review(
    hand_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取复盘"""
    service = FullHandService(db)
    
    try:
        review = service.get_review(hand_id, current_user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    
    action_log = [ActionRecord(**a) for a in review["action_log"]]
    
    # 构建 PreflopSpotReview 和 FlopSpotReview
    preflop_spot = None
    flop_spot = None
    
    if review.get("preflop_spot"):
        p = review["preflop_spot"]
        from app.schemas.fullhand import PreflopSpotReview
        preflop_spot = PreflopSpotReview(**p)
    
    if review.get("flop_spot"):
        f = review["flop_spot"]
        from app.schemas.fullhand import FlopSpotReview
        flop_spot = FlopSpotReview(**f)
    
    # 构建 ShowdownAnalysis
    showdown_analysis = None
    if review.get("showdown_analysis"):
        sa = review["showdown_analysis"]
        from app.schemas.fullhand import ShowdownAnalysis, PlayerShowdownResult
        
        players = [PlayerShowdownResult(**p) for p in sa.get("players", [])]
        showdown_analysis = ShowdownAnalysis(
            community_cards=sa.get("community_cards", []),
            pot=sa.get("pot", 0),
            players=players,
            winner_analysis=sa.get("winner_analysis"),
            explanation=sa.get("explanation", ""),
        )
    
    return FullHandReviewResponse(
        hand_id=review["hand_id"],
        result_bb=review["result_bb"],
        ended_by=review["ended_by"],
        action_log=action_log,
        preflop_spot=preflop_spot,
        flop_spot=flop_spot,
        can_replay=review["can_replay"],
        showdown_analysis=showdown_analysis,
    )


@router.post("/replay/{hand_id}", response_model=FullHandStartResponse)
def replay_hand(
    hand_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """重打同一手 (Pro)"""
    service = FullHandService(db)
    
    try:
        session = service.replay_hand(hand_id, current_user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN if "Pro" in str(e) else status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # 返回同 start
    state = GameState(
        status=session.status,
        street=session.current_street,
        players=[PlayerState(**p) for p in session.players],
        button_seat=session.button_seat,
        sb_seat=session.sb_seat,
        bb_seat=session.bb_seat,
        pot=session.pot,
        current_bet=session.current_bet,
        community_cards=session.community_cards,
        to_act_seat=session.hero_seat,
        hero_seat=session.hero_seat,
        hero_cards=session.hero_cards,
    )
    
    action_log = [ActionRecord(**a) for a in session.action_log]
    
    return FullHandStartResponse(
        hand_id=session.id,
        state=state,
        legal_actions=[],  # 需要重新计算
        action_log=action_log,
        is_key_spot=False,
    )


@router.get("/stats", response_model=FullHandStatsResponse)
def get_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取统计"""
    service = FullHandService(db)
    stats = service.get_stats(current_user)
    
    return FullHandStatsResponse(**stats)
