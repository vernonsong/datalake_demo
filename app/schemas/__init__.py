from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict


class HealthResponse(BaseModel):
    """心跳响应"""
    status: str
    timestamp: str
    service: str
    upstream: Optional[Dict[str, str]] = None


class RootResponse(BaseModel):
    """根路径响应"""
    service: str
    version: str
    status: str
