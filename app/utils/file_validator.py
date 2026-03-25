import os
import mimetypes
from pathlib import Path
from typing import List, Tuple, Optional
from fastapi import UploadFile, HTTPException
import logging

logger = logging.getLogger(__name__)


class FileValidator:
    
    MAGIC_NUMBERS = {
        '.xlsx': [
            b'\x50\x4B\x03\x04',
            b'\x50\x4B\x05\x06',
            b'\x50\x4B\x07\x08'
        ],
        '.xls': [
            b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1',
            b'\x09\x08\x10\x00\x00\x06\x05\x00'
        ],
        '.csv': []
    }
    
    ALLOWED_MIME_TYPES = {
        '.xlsx': [
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/zip'
        ],
        '.xls': [
            'application/vnd.ms-excel',
            'application/msexcel'
        ],
        '.csv': [
            'text/csv',
            'application/csv',
            'text/plain'
        ]
    }
    
    def __init__(
        self,
        allowed_extensions: List[str],
        max_file_size: int,
        allowed_mime_types: Optional[dict] = None
    ):
        self.allowed_extensions = [ext.lower() if ext.startswith('.') else f'.{ext.lower()}' for ext in allowed_extensions]
        self.max_file_size = max_file_size
        self.allowed_mime_types = allowed_mime_types or self.ALLOWED_MIME_TYPES
    
    def validate_filename(self, filename: str) -> Tuple[bool, Optional[str]]:
        if not filename:
            return False, "文件名不能为空"
        
        if len(filename) > 255:
            return False, "文件名过长（最大255字符）"
        
        dangerous_chars = ['..', '/', '\\', '\0', '<', '>', ':', '"', '|', '?', '*']
        for char in dangerous_chars:
            if char in filename:
                return False, f"文件名包含非法字符: {char}"
        
        return True, None
    
    def validate_extension(self, filename: str) -> Tuple[bool, Optional[str]]:
        ext = Path(filename).suffix.lower()
        
        if not ext:
            return False, "文件必须有扩展名"
        
        if ext not in self.allowed_extensions:
            return False, f"不支持的文件类型: {ext}，仅允许: {', '.join(self.allowed_extensions)}"
        
        return True, None
    
    def validate_mime_type(self, content_type: str, extension: str) -> Tuple[bool, Optional[str]]:
        if not content_type:
            return True, None
        
        ext = extension.lower() if extension.startswith('.') else f'.{extension.lower()}'
        
        allowed_types = self.allowed_mime_types.get(ext, [])
        if not allowed_types:
            return True, None
        
        if content_type not in allowed_types:
            logger.warning(f"MIME类型不匹配: {content_type} 不在允许列表 {allowed_types} 中")
        
        return True, None
    
    async def validate_magic_number(self, file: UploadFile, extension: str) -> Tuple[bool, Optional[str]]:
        ext = extension.lower() if extension.startswith('.') else f'.{extension.lower()}'
        
        magic_numbers = self.MAGIC_NUMBERS.get(ext, [])
        if not magic_numbers:
            return True, None
        
        try:
            header = await file.read(8)
            await file.seek(0)
            
            for magic in magic_numbers:
                if header.startswith(magic):
                    return True, None
            
            return False, f"文件头部验证失败，可能不是真实的{ext}文件"
        
        except Exception as e:
            logger.error(f"读取文件头部失败: {e}")
            return False, "文件读取失败"
    
    async def validate_file_size(self, file: UploadFile) -> Tuple[bool, Optional[str]]:
        try:
            content = await file.read()
            file_size = len(content)
            await file.seek(0)
            
            if file_size > self.max_file_size:
                size_mb = self.max_file_size / (1024 * 1024)
                return False, f"文件大小超过限制（最大{size_mb}MB）"
            
            if file_size == 0:
                return False, "文件为空"
            
            return True, None
        
        except Exception as e:
            logger.error(f"读取文件大小失败: {e}")
            return False, "文件读取失败"
    
    async def validate(self, file: UploadFile) -> Tuple[bool, Optional[str]]:
        is_valid, error = self.validate_filename(file.filename)
        if not is_valid:
            return False, error
        
        is_valid, error = self.validate_extension(file.filename)
        if not is_valid:
            return False, error
        
        extension = Path(file.filename).suffix
        
        is_valid, error = self.validate_mime_type(file.content_type, extension)
        if not is_valid:
            return False, error
        
        is_valid, error = await self.validate_file_size(file)
        if not is_valid:
            return False, error
        
        is_valid, error = await self.validate_magic_number(file, extension)
        if not is_valid:
            return False, error
        
        logger.info(f"文件验证通过: {file.filename}")
        return True, None
