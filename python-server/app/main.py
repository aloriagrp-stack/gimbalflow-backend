from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config.settings import settings
from app.config.db import init_db, is_mysql_active
from app.config.redis_cache import init_redis, get_redis_status

from app.routers.auth import router as auth_router
from app.routers.user import router as user_router
from app.routers.projects import router as projects_router
from app.routers.assets import router as assets_router
from app.routers.presets import router as presets_router
from app.routers.explore import router as explore_router
from app.routers.generation import router as generation_router
from app.routers.ml import router as ml_router
from app.routers.admin import router as admin_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("===================================================")
    print(f"[GimbalFlow] FastAPI Gateway running on port {settings.PORT}")
    print("===================================================")
    init_db()
    init_redis()
    yield
    # Shutdown
    print("[GimbalFlow] FastAPI Gateway shutting down")

app = FastAPI(
    title="GimbalFlow Backend API Gateway & ML Service",
    description="Unified high-performance Python FastAPI backend for GimbalFlow AI Video & Motion Director Platform.",
    version="2.0.0",
    lifespan=lifespan
)

# 1. CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Uploaded Media Static Files Mount (/uploads/...)
app.mount("/uploads", StaticFiles(directory=str(settings.UPLOADS_DIR)), name="uploads")

# 3. Register Routers
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(projects_router)
app.include_router(assets_router)
app.include_router(presets_router)
app.include_router(explore_router)
app.include_router(generation_router)
app.include_router(ml_router)
app.include_router(admin_router)

# 4. System Root Status
@app.get("/")
def root():
    return {
        "name": "GimbalFlow Backend API Gateway",
        "status": "online",
        "version": "2.0.0",
        "documentation": "/api/health"
    }

# 5. System Health Status
@app.get("/api/health")
def health():
    return {
        "status": "healthy",
        "gateway": "GimbalFlow FastAPI API Gateway",
        "mysql": "connected" if is_mysql_active() else "memory_fallback",
        "redis": get_redis_status(),
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
