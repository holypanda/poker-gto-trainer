from pydantic_settings import BaseSettings
from typing import Optional, List
import os


class Settings(BaseSettings):
    PROJECT_NAME: str = "Poker GTO Trainer"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "德州扑克翻前 GTO 训练模拟器 V1.0"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "sqlite:///./poker.db"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Security - SECRET_KEY must be set in environment
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # 30 minutes
    ALGORITHM: str = "HS256"
    
    # CORS - defaults to empty list, must be configured via env for production
    CORS_ORIGINS: str = ""
    
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
        env_file_encoding = "utf-8"
        extra = "ignore"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins from env or default"""
        cors_env = self.CORS_ORIGINS or os.getenv("CORS_ORIGINS", "")
        if cors_env:
            # Handle both JSON array format and comma-separated format
            cors_str = cors_env.strip()
            if cors_str.startswith("[") and cors_str.endswith("]"):
                import json
                try:
                    return json.loads(cors_str)
                except json.JSONDecodeError:
                    pass
            # Comma-separated format
            return [origin.strip() for origin in cors_str.split(",") if origin.strip()]
        return ["http://localhost:3000", "http://127.0.0.1:3000"] if self.DEBUG else []


settings = Settings()

# Validate SECRET_KEY is not the default or empty
if not settings.SECRET_KEY or settings.SECRET_KEY == "your-secret-key-change-in-production":
    raise ValueError(
        "SECRET_KEY must be set in environment variables and cannot be the default value. "
        "Please set a secure random string (at least 32 characters) in your .env file or environment."
    )
