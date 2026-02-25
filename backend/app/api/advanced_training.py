from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.base import get_db
from app.models.user import User
from app.api.deps import get_current_user
from app.services.advanced_training import AdvancedTrainingService
from app.services.user_service import can_train, consume_train_credit

router = APIRouter(prefix="/advanced", tags=["高级训练"])

# 内存中存储会话（生产环境应使用 Redis）
sessions = {}


@router.post("/start")
def start_advanced_training(
    stack_size: int = 100,
    scenario_count: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """开始高级模拟训练"""
    
    if not can_train(db, current_user):
        raise HTTPException(status_code=403, detail="训练次数不足")
    
    # 消耗训练次数
    consume_train_credit(db, current_user)
    
    # 创建训练服务
    service = AdvancedTrainingService(stack_size)
    
    # 生成场景
    scenarios = service.create_simulation_session(scenario_count)
    
    # 保存会话
    session_id = f"adv_{current_user.id}_{len(sessions)}"
    sessions[session_id] = {
        "user_id": current_user.id,
        "scenarios": scenarios,
        "current_index": 0,
        "correct_count": 0,
        "completed": False
    }
    
    return {
        "session_id": session_id,
        "scenarios": scenarios,
        "current_index": 0,
        "total": len(scenarios)
    }


@router.post("/answer/{session_id}")
def submit_advanced_answer(
    session_id: str,
    scenario_id: int,
    action: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """提交高级训练答案"""
    
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session["user_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # 获取当前场景
    scenarios = session["scenarios"]
    current_idx = session["current_index"]
    
    if current_idx >= len(scenarios):
        raise HTTPException(status_code=400, detail="Session completed")
    
    scenario = scenarios[current_idx]
    
    # 评估答案
    service = AdvancedTrainingService(scenario.get("stack_size", 100))
    result = service.evaluate_decision(scenario_id, action, scenario)
    
    # 更新统计
    if result["is_correct"]:
        session["correct_count"] += 1
    
    session["current_index"] += 1
    
    if session["current_index"] >= len(scenarios):
        session["completed"] = True
    
    return {
        "result": result,
        "progress": {
            "current": session["current_index"],
            "total": len(scenarios),
            "completed": session["completed"]
        }
    }


@router.get("/result/{session_id}")
def get_advanced_result(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """获取训练结果"""
    
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session["user_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    total = len(session["scenarios"])
    correct = session["correct_count"]
    accuracy = round(correct / total * 100, 1) if total > 0 else 0
    
    return {
        "total_scenarios": total,
        "correct_count": correct,
        "accuracy": accuracy,
        "completed": session["completed"]
    }
