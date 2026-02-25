"""
Poker GTO Trainer API V1.0
Production Ready
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.middleware import LoggingMiddleware, SecurityHeadersMiddleware
from app.db.base import engine, Base
from app.api import auth, training, payment, admin, advanced_training, fullhand


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时创建数据库表
    Base.metadata.create_all(bind=engine)
    print(f"🚀 {settings.PROJECT_NAME} V{settings.VERSION} started")
    yield
    # 关闭时清理
    print(f"👋 {settings.PROJECT_NAME} shutting down")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# 中间件 (按执行顺序，后添加的先执行)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=3600,
)

# 注册路由
app.include_router(auth.router, prefix="/api/v1")
app.include_router(training.router, prefix="/api/v1")
app.include_router(advanced_training.router, prefix="/api/v1")
app.include_router(fullhand.router, prefix="/api/v1")
app.include_router(payment.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")


@app.get("/")
def root():
    """API 根路径"""
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "description": settings.DESCRIPTION,
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "timestamp": __import__('datetime').datetime.utcnow().isoformat()
    }


@app.get("/api/v1/health/detailed")
def health_detailed():
    """详细健康检查"""
    import psycopg2
    from sqlalchemy import text
    
    health_status = {
        "status": "healthy",
        "version": settings.VERSION,
        "timestamp": __import__('datetime').datetime.utcnow().isoformat(),
        "services": {}
    }
    
    # 检查数据库
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            health_status["services"]["database"] = "connected"
    except Exception as e:
        health_status["services"]["database"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    return health_status
