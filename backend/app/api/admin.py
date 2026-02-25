from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from app.db.base import get_db
from app.models.user import User
from app.models.training_session import TrainingSession
from app.models.training_record import TrainingRecord
from app.models.subscription import Subscription
from app.api.deps import get_current_user

router = APIRouter(prefix="/admin", tags=["管理后台"])


def check_admin(user: User):
    """检查是否为管理员"""
    # 简单实现：第一个用户或特定邮箱为管理员
    admin_emails = ["admin@poker.com", "admin@test.com"]
    if user.email not in admin_emails and user.id != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )


@router.get("/dashboard")
def admin_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """管理后台仪表盘数据"""
    check_admin(current_user)
    
    # 用户统计
    total_users = db.query(User).count()
    today_users = db.query(User).filter(
        func.date(User.created_at) == func.date(func.now())
    ).count()
    
    # VIP 统计
    vip_users = db.query(User).filter(User.is_subscribed == True).count()
    
    # 训练统计
    total_trains = db.query(TrainingRecord).count()
    today_trains = db.query(TrainingRecord).filter(
        func.date(TrainingRecord.created_at) == func.date(func.now())
    ).count()
    
    # 收入统计
    total_revenue = db.query(func.sum(Subscription.amount)).filter(
        Subscription.status == "active"
    ).scalar() or 0
    
    # 最近 7 天训练趋势
    last_7_days = []
    for i in range(6, -1, -1):
        date = datetime.utcnow().date() - timedelta(days=i)
        count = db.query(TrainingRecord).filter(
            func.date(TrainingRecord.created_at) == date
        ).count()
        last_7_days.append({
            "date": date.strftime("%m-%d"),
            "count": count
        })
    
    return {
        "users": {
            "total": total_users,
            "today": today_users,
            "vip": vip_users
        },
        "training": {
            "total": total_trains,
            "today": today_trains
        },
        "revenue": {
            "total": round(total_revenue, 2)
        },
        "trend": last_7_days
    }


@router.get("/users")
def admin_users(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户列表"""
    check_admin(current_user)
    
    users = db.query(User).order_by(User.created_at.desc()).offset(skip).limit(limit).all()
    
    return [{
        "id": u.id,
        "username": u.username,
        "email": u.email,
        "is_subscribed": u.is_subscribed,
        "total_trains": u.total_trains,
        "accuracy": u.accuracy,
        "created_at": u.created_at.isoformat() if u.created_at else None
    } for u in users]


@router.post("/users/{user_id}/make-vip")
def make_user_vip(
    user_id: int,
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """手动给用户开通 VIP"""
    check_admin(current_user)
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_subscribed = True
    user.subscription_expires_at = datetime.utcnow() + timedelta(days=days)
    
    db.commit()
    
    return {"success": True, "message": f"User {user.username} is now VIP for {days} days"}


@router.get("/stats")
def admin_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """详细统计"""
    check_admin(current_user)
    
    # 位置统计
    position_stats = db.query(
        TrainingRecord.position,
        func.count().label("total"),
        func.sum(func.cast(TrainingRecord.is_correct, db.Integer)).label("correct")
    ).group_by(TrainingRecord.position).all()
    
    # 手牌类型统计
    hand_types = {}
    records = db.query(TrainingRecord).all()
    for r in records:
        hand = r.hand
        if len(hand) == 2:
            ht = "pair"
        elif hand.endswith('s'):
            ht = "suited"
        else:
            ht = "offsuit"
        
        if ht not in hand_types:
            hand_types[ht] = {"total": 0, "correct": 0}
        hand_types[ht]["total"] += 1
        if r.is_correct:
            hand_types[ht]["correct"] += 1
    
    return {
        "positions": [
            {"name": p.position, "total": p.total, "correct": p.correct or 0}
            for p in position_stats
        ],
        "hand_types": hand_types
    }
