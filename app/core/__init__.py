from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.settings import settings
import asyncio
import logging

logger = logging.getLogger(__name__)


async def cleanup_files_task():
    """定期清理过期文件的后台任务"""
    from app.utils.file_storage import FileStorage
    
    file_storage = FileStorage(
        temp_dir=settings.file_upload_temp_dir,
        cleanup_after_hours=settings.file_upload_cleanup_hours
    )
    
    while True:
        try:
            await asyncio.sleep(3600)
            logger.info("开始清理过期文件...")
            file_storage.cleanup_old_files()
        except Exception as e:
            logger.error(f"清理文件任务出错: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    settings.debug and print(f"[{settings.app_name}] 服务启动...")
    
    # 加载工作流
    from app.workflows.loader import load_all_workflows
    load_all_workflows()
    
    cleanup_task = None
    if settings.file_upload_enabled:
        cleanup_task = asyncio.create_task(cleanup_files_task())
        logger.info("文件清理后台任务已启动")
    
    yield
    
    if cleanup_task:
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            logger.info("文件清理后台任务已停止")
    
    settings.debug and print(f"[{settings.app_name}] 服务关闭...")
