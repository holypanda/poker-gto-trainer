import json
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict
from sqlalchemy.orm import Session
from alipay import AliPay
from app.models.subscription import Subscription
from app.models.user import User
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class PaymentService:
    def __init__(self):
        self.alipay = None
        if settings.ALIPAY_APP_ID and settings.ALIPAY_PRIVATE_KEY:
            self.alipay = AliPay(
                appid=settings.ALIPAY_APP_ID,
                app_notify_url=None,  # 异步通知 URL 将在创建订单时设置
                app_private_key_string=settings.ALIPAY_PRIVATE_KEY,
                alipay_public_key_string=settings.ALIPAY_PUBLIC_KEY,
                sign_type="RSA2",
                debug=False  # 生产环境设置为 False
            )
    
    def create_subscription_order(
        self,
        db: Session,
        user: User,
        return_url: str,
        notify_url: str
    ) -> Dict:
        """创建订阅订单"""
        
        # 创建订单号
        out_trade_no = f"POKER_{user.id}_{int(datetime.utcnow().timestamp())}"
        
        # 创建订阅记录
        subscription = Subscription(
            user_id=user.id,
            amount=settings.SUBSCRIPTION_PRICE,
            currency=settings.SUBSCRIPTION_CURRENCY,
            status="pending"
        )
        db.add(subscription)
        db.commit()
        db.refresh(subscription)
        
        # 更新订单号
        order_id = f"{out_trade_no}_{subscription.id}"
        
        if not self.alipay:
            logger.warning("Alipay not configured, returning mock payment")
            return {
                "order_id": order_id,
                "payment_url": None,
                "qr_code": None,
                "mock": True
            }
        
        # 创建支付宝订单
        try:
            order_string = self.alipay.api_alipay_trade_page_pay(
                out_trade_no=order_id,
                total_amount=str(settings.SUBSCRIPTION_PRICE),
                subject=f"Poker GTO Trainer - 月度订阅",
                body=f"用户: {user.username}, 订阅时长: 1个月",
                return_url=return_url,
                notify_url=notify_url
            )
            
            payment_url = f"{settings.ALIPAY_GATEWAY}?{order_string}"
            
            return {
                "order_id": order_id,
                "payment_url": payment_url,
                "qr_code": None
            }
            
        except Exception as e:
            logger.error(f"Failed to create Alipay order: {e}")
            # 回滚订阅记录
            db.delete(subscription)
            db.commit()
            raise
    
    def process_alipay_notify(self, db: Session, notify_data: Dict) -> bool:
        """处理支付宝异步通知"""
        
        if not self.alipay:
            logger.warning("Alipay not configured")
            return False
        
        # 验证签名
        signature = notify_data.pop("sign", None)
        success = self.alipay.verify(notify_data, signature)
        
        if not success:
            logger.warning("Alipay signature verification failed")
            return False
        
        # 获取订单信息
        out_trade_no = notify_data.get("out_trade_no")
        trade_no = notify_data.get("trade_no")
        trade_status = notify_data.get("trade_status")
        total_amount = notify_data.get("total_amount")
        buyer_id = notify_data.get("buyer_id")
        gmt_payment = notify_data.get("gmt_payment")
        
        # 查找订阅记录
        subscription = db.query(Subscription).filter(
            Subscription.id == int(out_trade_no.split("_")[-1])
        ).first()
        
        if not subscription:
            logger.error(f"Subscription not found: {out_trade_no}")
            return False
        
        # 验证金额
        if float(total_amount) != subscription.amount:
            logger.error(f"Amount mismatch: {total_amount} != {subscription.amount}")
            return False
        
        # 处理支付状态
        if trade_status in ["TRADE_SUCCESS", "TRADE_FINISHED"]:
            # 支付成功
            subscription.status = "active"
            subscription.alipay_trade_no = trade_no
            subscription.alipay_buyer_id = buyer_id
            subscription.started_at = datetime.utcnow()
            subscription.expires_at = datetime.utcnow() + timedelta(days=30)
            
            # 更新用户订阅状态
            user = db.query(User).filter(User.id == subscription.user_id).first()
            if user:
                user.is_subscribed = True
                user.subscription_expires_at = subscription.expires_at
            
            db.commit()
            logger.info(f"Subscription activated: {subscription.id}")
            return True
            
        elif trade_status == "TRADE_CLOSED":
            # 交易关闭
            subscription.status = "cancelled"
            db.commit()
            return True
        
        return False
    
    def verify_payment(self, db: Session, order_id: str) -> bool:
        """主动查询支付状态"""
        
        if not self.alipay:
            # 模拟支付成功 (开发环境)
            subscription = db.query(Subscription).filter(
                Subscription.id == int(order_id.split("_")[-1])
            ).first()
            
            if subscription and subscription.status == "pending":
                subscription.status = "active"
                subscription.started_at = datetime.utcnow()
                subscription.expires_at = datetime.utcnow() + timedelta(days=30)
                
                user = db.query(User).filter(User.id == subscription.user_id).first()
                if user:
                    user.is_subscribed = True
                    user.subscription_expires_at = subscription.expires_at
                
                db.commit()
                return True
            
            return subscription.status == "active" if subscription else False
        
        try:
            result = self.alipay.api_alipay_trade_query(out_trade_no=order_id)
            
            if result.get("code") == "10000":
                trade_status = result.get("trade_status")
                
                subscription = db.query(Subscription).filter(
                    Subscription.id == int(order_id.split("_")[-1])
                ).first()
                
                if not subscription:
                    return False
                
                if trade_status in ["TRADE_SUCCESS", "TRADE_FINISHED"]:
                    if subscription.status != "active":
                        subscription.status = "active"
                        subscription.alipay_trade_no = result.get("trade_no")
                        subscription.started_at = datetime.utcnow()
                        subscription.expires_at = datetime.utcnow() + timedelta(days=30)
                        
                        user = db.query(User).filter(User.id == subscription.user_id).first()
                        if user:
                            user.is_subscribed = True
                            user.subscription_expires_at = subscription.expires_at
                        
                        db.commit()
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to query payment: {e}")
            return False
    
    def cancel_subscription(self, db: Session, user: User) -> bool:
        """取消订阅 (到期不续费)"""
        
        subscription = db.query(Subscription).filter(
            Subscription.user_id == user.id,
            Subscription.status == "active"
        ).order_by(Subscription.expires_at.desc()).first()
        
        if subscription:
            subscription.status = "cancelled"
            db.commit()
            return True
        
        return False
    
    def check_subscription_status(self, db: Session, user: User) -> Dict:
        """检查订阅状态"""
        
        now = datetime.utcnow()
        
        # 检查是否过期
        if user.is_subscribed and user.subscription_expires_at:
            if user.subscription_expires_at < now:
                user.is_subscribed = False
                db.commit()
        
        active_subscription = db.query(Subscription).filter(
            Subscription.user_id == user.id,
            Subscription.status == "active",
            Subscription.expires_at > now
        ).order_by(Subscription.expires_at.desc()).first()
        
        if active_subscription:
            return {
                "is_subscribed": True,
                "expires_at": active_subscription.expires_at,
                "days_remaining": (active_subscription.expires_at - now).days
            }
        
        return {
            "is_subscribed": False,
            "expires_at": None,
            "days_remaining": 0
        }


# 全局支付服务实例
payment_service = PaymentService()
