from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class SubscriptionBase(BaseModel):
    amount: float
    currency: str = "CNY"


class SubscriptionCreate(SubscriptionBase):
    pass


class PaymentRequest(BaseModel):
    return_url: str
    notify_url: str


class PaymentResponse(BaseModel):
    order_id: str
    payment_url: Optional[str] = None
    qr_code: Optional[str] = None  # 用于扫码支付


class SubscriptionResponse(BaseModel):
    id: int
    user_id: int
    amount: float
    currency: str
    status: str
    started_at: Optional[datetime]
    expires_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class AlipayNotify(BaseModel):
    # 支付宝异步通知参数
    app_id: str
    out_trade_no: str
    trade_no: str
    trade_status: str
    total_amount: str
    buyer_id: Optional[str] = None
    gmt_payment: Optional[str] = None
