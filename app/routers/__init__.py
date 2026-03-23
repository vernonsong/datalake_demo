from fastapi import APIRouter, Depends
from datetime import datetime
from app.schemas import HealthResponse, RootResponse
from app.settings import settings
from app.core.dependencies import get_metadata_client
from app.core.clients.base_client import BaseClient


router = APIRouter()


@router.get("/", response_model=RootResponse)
def root():
    """根路径"""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "running"
    }


@router.get("/health", response_model=HealthResponse)
def health_check(metadata_client: BaseClient = Depends(get_metadata_client)):
    """心跳接口"""
    upstream_status = "unknown"
    try:
        result = metadata_client.request("GET", "/api/metadata/databases")
        if result.get("databases") is not None:
            upstream_status = "healthy"
        else:
            upstream_status = "unhealthy"
    except Exception:
        upstream_status = "error"

    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "datalake-platform",
        "upstream": {
            "metadata": upstream_status
        }
    }
