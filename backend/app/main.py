"""实验室样品检测管理平台 后端服务入口。

启动：uvicorn app.main:app --host 127.0.0.1 --port 8000
健康检查：GET /api/health
"""
from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import ROUTERS
from app.store import RANGE_CHOICES, store

app = FastAPI(title="实验室样品检测管理平台", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for module in ROUTERS:
    app.include_router(module.router)


@app.get("/api/health")
def health() -> dict[str, object]:
    """健康检查：确认服务已经监听、示例数据已经就绪。"""
    return {"ok": True, "app": settings.app_name, "modules": len(store.module_names())}


@app.get("/api/overview")
def overview(range: str = "all") -> dict[str, object]:
    """运营概览：按统计区间（today/7d/30d/all）汇总各模块看板数据。"""
    if range not in RANGE_CHOICES:
        raise HTTPException(
            status_code=400,
            detail=f"统计区间仅支持：{ '、'.join(RANGE_CHOICES) }",
        )
    return store.overview(range)
