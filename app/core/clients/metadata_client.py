#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
元数据服务客户端
只封装通用请求方法，完全解耦
"""

from typing import Optional, Dict, Any, Callable
from app.core.clients.base_client import BaseClient


class MetadataClient(BaseClient):
    """元数据服务客户端"""

    def __init__(
        self,
        base_url: str,
        timeout: int = 30,
        token_provider: Optional[Callable[[], str]] = None
    ):
        """初始化元数据服务客户端

        Args:
            base_url: 服务基础URL
            timeout: 请求超时时间（秒）
            token_provider: 获取Token的回调函数
        """
        super().__init__(base_url, timeout, token_provider)
