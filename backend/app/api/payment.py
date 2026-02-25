from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.db.base import get_db
from app.models.user import User
from app.api.deps import get_current_user
from app.schemas.subscription import PaymentRequest, PaymentResponse, SubscriptionResponse
from app.services.payment_service import payment_service

router = APIRouter(prefix="/payment", tags=["支付"])


@router.post("/subscribe", response_model=PaymentResponse)
def create_subscription(
    request: Request,
    payment_req: PaymentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建订阅订单"""
    
    # 构建回调 URL
    base_url = str(request.base_url).rstrip('/')
    return_url = payment_req.return_url or f"{base_url}/payment/success"
    notify_url = payment_req.notify_url or f"{base_url}/api/v1/payment/notify"
    
    try:
        result = payment_service.create_subscription_order(
            db, current_user, return_url, notify_url
        )
        
        return PaymentResponse(
            order_id=result["order_id"],
            payment_url=result.get("payment_url"),
            qr_code=result.get("qr_code")
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create order: {str(e)}"
        )


@router.post("/notify")
async def alipay_notify(request: Request, db: Session = Depends(get_db)):
    """支付宝异步通知回调"""
    
    # 获取所有表单数据
    form_data = dict(await request.form())
    
    success = payment_service.process_alipay_notify(db, form_data)
    
    if success:
        return "success"  # 支付宝要求返回 success
    else:
        return "fail"


@router.get("/verify/{order_id}")
def verify_payment(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """验证支付状态"""
    success = payment_service.verify_payment(db, order_id)
    
    return {"success": success}


@router.get("/status")
def get_subscription_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取订阅状态"""
    status = payment_service.check_subscription_status(db, current_user)
    
    return status


@router.post("/cancel")
def cancel_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """取消订阅 (到期不续费)"""
    success = payment_service.cancel_subscription(db, current_user)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active subscription found"
        )
    
    return {"success": True, "message": "Subscription will not renew"}


# 修复 alipay_notify 函数，添加 await
