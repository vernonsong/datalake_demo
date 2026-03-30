#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQL服务集成测试
"""

import json
import sys
import os
import unittest
import threading
import time
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

class TestSqlServiceIntegration(unittest.TestCase):
    """SQL服务集成测试"""

    @classmethod
    def setUpClass(cls):
        """启动Mock API服务器"""
        os.environ.setdefault("MOCK_API_SECRET", "mock-secret-key-12345")
        os.environ.setdefault("JWT_SECRET", "jwt-secret-key-for-token-generation")
        os.environ.setdefault("ALI_API_KEY", "test-ali-api-key")
        from mock_service.api_server import run_api_server
        # Use a different port to avoid conflict
        cls.port = 5003
        cls.server_thread = threading.Thread(target=run_api_server, args=(cls.port,))
        cls.server_thread.daemon = True
        cls.server_thread.start()
        time.sleep(1)
        cls.base_url = f"http://localhost:{cls.port}"
        cls.token = cls._get_token()

    @classmethod
    def _get_token(cls):
        """获取Token"""
        response = requests.post(
            f"{cls.base_url}/api/token",
            json={"secret": "mock-secret-key-12345"}
        )
        if response.status_code == 200:
            return response.json().get("token")
        return None

    def _get_headers(self):
        """获取带鉴权的headers"""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    def test_sql_request(self):
        """测试提交SQL请求"""
        payload = {
            "sql": "SELECT * FROM users",
            "database": "main_db"
        }
        response = requests.post(
            f"{self.base_url}/api/sql/request",
            json=payload,
            headers=self._get_headers()
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["data"]["sql"], "SELECT * FROM users")

if __name__ == "__main__":
    unittest.main()
