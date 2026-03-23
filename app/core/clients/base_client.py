#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基础客户端类
提供统一的请求方法接口，支持Token鉴权
"""

import requests
import logging
from typing import Dict, Any, Optional, Callable

logger = logging.getLogger(__name__)


class BaseClient:
    """基础客户端类"""

    def __init__(
        self,
        base_url: str,
        timeout: int = 30,
        token_provider: Optional[Callable[[], str]] = None
    ):
        """初始化客户端

        Args:
            base_url: 服务基础URL
            timeout: 请求超时时间（秒）
            token_provider: 获取Token的回调函数
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.token_provider = token_provider
        self.session = requests.Session()

    def _get_auth_headers(self) -> Dict[str, str]:
        """获取认证头"""
        if self.token_provider:
            token = self.token_provider()
            if token:
                return {"Authorization": f"Bearer {token}"}
        return {}

    def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        use_auth: bool = True
    ) -> Dict[str, Any]:
        """统一的请求方法

        Args:
            method: 请求类型 (GET, POST, PUT, DELETE, PATCH)
            endpoint: 端点路径
            params: URL参数
            data: 表单数据
            json: JSON数据
            headers: 请求头
            use_auth: 是否使用认证

        Returns:
            响应数据
        """
        url = f"{self.base_url}{endpoint}"

        request_headers = {}
        if use_auth:
            request_headers.update(self._get_auth_headers())
        if headers:
            request_headers.update(headers)

        logger.info(f"发送请求: {method} {url}")
        logger.debug(f"请求参数: params={params}, data={data}, json={json}")

        try:
            response = self.session.request(
                method=method.upper(),
                url=url,
                params=params,
                data=data,
                json=json,
                headers=request_headers,
                timeout=self.timeout
            )

            if response.status_code == 401 and use_auth and self.token_provider:
                token_provider_self = getattr(self.token_provider, "__self__", None)
                if token_provider_self and hasattr(token_provider_self, "clear_token"):
                    token_provider_self.clear_token()
                    request_headers = {}
                    request_headers.update(self._get_auth_headers())
                    if headers:
                        request_headers.update(headers)
                    response = self.session.request(
                        method=method.upper(),
                        url=url,
                        params=params,
                        data=data,
                        json=json,
                        headers=request_headers,
                        timeout=self.timeout
                    )

            response.raise_for_status()

            result = response.json()
            logger.info(f"请求成功: {method} {url}")
            logger.debug(f"响应数据: {result}")

            return result

        except requests.exceptions.Timeout:
            logger.error(f"请求超时: {method} {url}")
            return {"success": False, "error": "请求超时"}
        except requests.exceptions.ConnectionError:
            logger.error(f"连接错误: {method} {url}")
            return {"success": False, "error": "连接错误"}
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP错误: {method} {url}, {e}")
            return {"success": False, "error": f"HTTP错误: {e}"}
        except Exception as e:
            logger.error(f"请求异常: {method} {url}, {e}")
            return {"success": False, "error": f"请求异常: {e}"}

    def close(self):
        """关闭会话"""
        self.session.close()
