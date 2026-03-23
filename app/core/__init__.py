from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    settings.debug and print(f"[{settings.app_name}] 服务启动...")
    yield
    settings.debug and print(f"[{settings.app_name}] 服务关闭...")
