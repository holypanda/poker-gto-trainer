from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "Poker GTO Trainer"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "德州扑克翻前 GTO 训练模拟器 V1.0"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "sqlite:///./poker.db"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    ALGORITHM: str = "HS256"
    
    # CORS - 允许所有来源（生产环境建议限制具体域名）
    CORS_ORIGINS: list = ["*"]
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 60  # seconds
    
    # Alipay
    ALIPAY_APP_ID: Optional[str] = None
    ALIPAY_PRIVATE_KEY: Optional[str] = None
    ALIPAY_PUBLIC_KEY: Optional[str] = None
    ALIPAY_GATEWAY: str = "https://openapi.alipay.com/gateway.do"
    
    # Subscription
    SUBSCRIPTION_PRICE: float = 1.0  # 1元/月
    SUBSCRIPTION_CURRENCY: str = "CNY"
    
    # Training
    DEFAULT_DAILY_FREE_TRAINS: int = 20
    SUBSCRIBER_DAILY_TRAINS: int = 999999
    
    class Config:
        env_file = ".env"


settings = Settings()
