import os
import shutil
from pathlib import Path
from typing import Optional
from uuid import uuid4
from datetime import datetime, timedelta
from fastapi import UploadFile
import logging

logger = logging.getLogger(__name__)


class FileStorage:
    
    def __init__(self, temp_dir: str, cleanup_after_hours: int = 24):
        self.temp_dir = Path(temp_dir)
        self.cleanup_after_hours = cleanup_after_hours
        self._ensure_temp_dir()
    
    def _ensure_temp_dir(self):
        if not self.temp_dir.exists():
            self.temp_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"创建临时目录: {self.temp_dir}")
    
    def generate_safe_filename(self, original_filename: str) -> tuple[str, str]:
        ext = Path(original_filename).suffix
        file_id = uuid4().hex
        safe_filename = f"{file_id}{ext}"
        return file_id, safe_filename
    
    async def save_file(self, file: UploadFile) -> tuple[str, str, int]:
        file_id, safe_filename = self.generate_safe_filename(file.filename)
        file_path = self.temp_dir / safe_filename
        
        try:
            content = await file.read()
            file_size = len(content)
            
            with open(file_path, 'wb') as f:
                f.write(content)
            
            os.chmod(file_path, 0o444)
            
            logger.info(f"文件保存成功: {file.filename} -> {safe_filename} ({file_size} bytes)")
            return file_id, str(file_path), file_size
        
        except Exception as e:
            logger.error(f"文件保存失败: {e}")
            if file_path.exists():
                file_path.unlink()
            raise
    
    def get_file_path(self, file_id: str, extension: str) -> Optional[Path]:
        safe_filename = f"{file_id}{extension}"
        file_path = self.temp_dir / safe_filename
        
        if file_path.exists():
            return file_path
        return None
    
    def delete_file(self, file_id: str, extension: str) -> bool:
        file_path = self.get_file_path(file_id, extension)
        
        if file_path and file_path.exists():
            try:
                os.chmod(file_path, 0o644)
                file_path.unlink()
                logger.info(f"文件删除成功: {file_id}")
                return True
            except Exception as e:
                logger.error(f"文件删除失败: {e}")
                return False
        return False
    
    def cleanup_old_files(self):
        if not self.temp_dir.exists():
            return
        
        cutoff_time = datetime.now() - timedelta(hours=self.cleanup_after_hours)
        deleted_count = 0
        
        for file_path in self.temp_dir.iterdir():
            if file_path.is_file():
                file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                
                if file_mtime < cutoff_time:
                    try:
                        os.chmod(file_path, 0o644)
                        file_path.unlink()
                        deleted_count += 1
                        logger.info(f"清理过期文件: {file_path.name}")
                    except Exception as e:
                        logger.error(f"清理文件失败: {file_path.name}, {e}")
        
        if deleted_count > 0:
            logger.info(f"清理完成，共删除 {deleted_count} 个过期文件")
