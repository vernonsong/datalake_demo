#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Token服务 - 生成和验证动态Token
"""

import hmac
import hashlib
import time
import base64
import os
from dotenv import load_dotenv

load_dotenv()


class TokenService:
    """Token服务"""

    def __init__(self, secret: str = None, expires_in: int = 3600):
        """初始化Token服务

        Args:
            secret: 密钥，用于生成token
            expires_in: token过期时间（秒）
        """
        self.secret = secret or os.getenv("JWT_SECRET", "default-secret")
        self.expires_in = expires_in

    def generate_token(self, payload: dict = None) -> str:
        """生成动态Token

        使用HMAC-SHA256生成包含时间戳的token

        Args:
            payload: 额外载荷数据

        Returns:
            动态token字符串
        """
        timestamp = int(time.time())
        exp = timestamp + self.expires_in

        base_message = f"{timestamp}.{exp}"

        payload_b64 = ""
        if payload:
            payload_b64 = base64.b64encode(str(payload).encode()).decode()
            base_message = f"{base_message}.{payload_b64}"

        signature = hmac.new(
            self.secret.encode(),
            base_message.encode(),
            hashlib.sha256
        ).hexdigest()

        token = f"{base_message}.{signature}"
        return token

    def verify_token(self, token: str) -> bool:
        """验证Token是否有效

        Args:
            token: 待验证的token

        Returns:
            是否有效
        """
        try:
            if not token or not isinstance(token, str):
                return False

            parts = token.split(".")
            if len(parts) < 3:
                return False

            timestamp = int(parts[0])
            exp = int(parts[1])
            signature = parts[-1]

            if exp < int(time.time()):
                return False

            payload_b64 = ""
            if len(parts) > 3:
                payload_b64 = parts[2]

            message = f"{timestamp}.{exp}"
            if payload_b64:
                message = f"{message}.{payload_b64}"

            expected_signature = hmac.new(
                self.secret.encode(),
                message.encode(),
                hashlib.sha256
            ).hexdigest()

            return hmac.compare_digest(signature, expected_signature)

        except (ValueError, TypeError, AttributeError, IndexError):
            return False

    def verify_token_with_payload(self, token: str) -> tuple[bool, dict]:
        """验证Token并返回载荷

        Args:
            token: 待验证的token

        Returns:
            (是否有效, 载荷数据)
        """
        if not self.verify_token(token):
            return False, {}

        try:
            parts = token.split(".")
            if len(parts) > 3 and parts[2]:
                payload_b64 = parts[2]
                payload_str = base64.b64decode(payload_b64.encode()).decode()
                return True, eval(payload_str)
            return True, {}
        except Exception:
            return False, {}

    def extract_timestamp(self, token: str) -> int:
        """从token中提取时间戳

        Args:
            token: token字符串

        Returns:
            生成时的时间戳
        """
        try:
            parts = token.split(".")
            if len(parts) >= 2:
                return int(parts[0])
        except Exception:
            pass
        return 0


_token_service: TokenService = None


def get_token_service() -> TokenService:
    """获取Token服务单例"""
    global _token_service
    if _token_service is None:
        _token_service = TokenService()
    return _token_service
