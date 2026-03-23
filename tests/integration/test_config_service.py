#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置中心服务集成测试
"""

import json
import sys
import os
import unittest
import threading
import time
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mock_service.config_service import ConfigService


class TestConfigServiceIntegration(unittest.TestCase):
    """配置中心服务集成测试"""

    @classmethod
    def setUpClass(cls):
        """启动Mock API服务器"""
        os.environ.setdefault("MOCK_API_SECRET", "mock-secret-key-12345")
        os.environ.setdefault("JWT_SECRET", "jwt-secret-key-for-token-generation")
        os.environ.setdefault("ALI_API_KEY", "test-ali-api-key")
        from mock_service.api_server import run_api_server
        cls.server_thread = threading.Thread(target=run_api_server, args=(5002,))
        cls.server_thread.daemon = True
        cls.server_thread.start()
        time.sleep(1)
        cls.base_url = "http://localhost:5002"
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

    def test_get_all_configs(self):
        """测试获取所有敏感配置"""
        response = requests.get(f"{self.base_url}/api/config")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("configs", data)
        self.assertIn("jwt_secret", data["configs"])
        self.assertIn("mock_api_secret", data["configs"])
        self.assertIn("ali_api_key", data["configs"])

    def test_get_single_config(self):
        """测试获取单个敏感配置"""
        response = requests.get(f"{self.base_url}/api/config/jwt_secret")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["key"], "jwt_secret")
        self.assertIn("value", data)

    def test_get_nonexistent_config(self):
        """测试获取不存在的配置"""
        response = requests.get(
            f"{self.base_url}/api/config/nonexistent",
            headers=self._get_headers()
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("error", data)

    def test_set_config(self):
        """测试设置敏感配置"""
        new_config = {
            "key": "test_key",
            "value": "test_value"
        }
        response = requests.post(
            f"{self.base_url}/api/config",
            json=new_config,
            headers=self._get_headers()
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["key"], "test_key")

    def test_set_config_missing_key(self):
        """测试设置配置-缺少key"""
        response = requests.post(
            f"{self.base_url}/api/config",
            json={"value": {"test": "data"}},
            headers=self._get_headers()
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("error", data)

    def test_update_config(self):
        """测试更新配置"""
        response = requests.put(
            f"{self.base_url}/api/config/jwt_secret",
            json={"value": "new-secret-value"},
            headers=self._get_headers()
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")

    def test_delete_config(self):
        """测试删除配置"""
        response = requests.delete(
            f"{self.base_url}/api/config/jwt_secret",
            headers=self._get_headers()
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")

    def test_dependency_get_ali_api_key_with_real_config_center(self):
        """测试依赖注入通过真实配置中心获取ali_api_key"""
        from app.core import dependencies
        from app.settings import settings
        old_url = settings.mock_service_url
        old_secret = settings.mock_api_secret
        old_provider = dependencies._token_provider
        dependencies._token_provider = None
        settings.mock_service.MOCK_SERVICE_URL = self.base_url
        settings.mock_service.MOCK_API_SECRET = "mock-secret-key-12345"
        try:
            key = dependencies.get_ali_api_key()
        finally:
            settings.mock_service.MOCK_SERVICE_URL = old_url
            settings.mock_service.MOCK_API_SECRET = old_secret
            dependencies._token_provider = old_provider
        self.assertTrue(key)

    def test_health_check(self):
        """测试健康检查"""
        response = requests.get(f"{self.base_url}/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")


class TestConfigServiceUnit(unittest.TestCase):
    """配置中心服务单元测试"""

    def setUp(self):
        """每个测试前创建新的ConfigService实例"""
        os.environ["MOCK_API_SECRET"] = "mock-secret-key-12345"
        os.environ["JWT_SECRET"] = "jwt-secret-key-for-token-generation"
        os.environ["ALI_API_KEY"] = "unit-test-ali-api-key"
        self.config_service = ConfigService()

    def test_get_all_configs(self):
        """测试获取所有敏感配置"""
        result = self.config_service.get_all_configs()
        self.assertIn("configs", result)
        self.assertIn("jwt_secret", result["configs"])
        self.assertIn("mock_api_secret", result["configs"])
        self.assertIn("ali_api_key", result["configs"])

    def test_get_config_existing(self):
        """测试获取已存在的敏感配置"""
        result = self.config_service.get_config("jwt_secret")
        self.assertEqual(result["key"], "jwt_secret")
        self.assertIn("value", result)

    def test_load_ali_api_key_from_env(self):
        """测试ali_api_key从环境变量加载"""
        result = self.config_service.get_config("ali_api_key")
        self.assertEqual(result["value"], "unit-test-ali-api-key")

    def test_get_config_nonexisting(self):
        """测试获取不存在的配置"""
        result = self.config_service.get_config("nonexistent")
        self.assertIn("error", result)

    def test_set_config(self):
        """测试设置敏感配置"""
        result = self.config_service.set_config("test_key", "test_value")
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["key"], "test_key")

    def test_delete_config_existing(self):
        """测试删除已存在的配置"""
        self.config_service.set_config("to_delete", "value")
        result = self.config_service.delete_config("to_delete")
        self.assertEqual(result["status"], "success")

    def test_delete_config_nonexisting(self):
        """测试删除不存在的配置"""
        result = self.config_service.delete_config("nonexistent")
        self.assertIn("error", result)

    def test_init_failed_when_ali_api_key_missing(self):
        """测试缺少ali_api_key时初始化失败"""
        previous_value = os.environ.get("ALI_API_KEY")
        os.environ["ALI_API_KEY"] = ""
        try:
            with self.assertRaises(ValueError):
                ConfigService()
        finally:
            if previous_value is None:
                os.environ.pop("ALI_API_KEY", None)
            else:
                os.environ["ALI_API_KEY"] = previous_value

    def test_init_failed_when_jwt_secret_missing(self):
        """测试缺少jwt_secret时初始化失败"""
        previous_value = os.environ.get("JWT_SECRET")
        os.environ["JWT_SECRET"] = ""
        try:
            with self.assertRaises(ValueError):
                ConfigService()
        finally:
            if previous_value is None:
                os.environ.pop("JWT_SECRET", None)
            else:
                os.environ["JWT_SECRET"] = previous_value

    def test_init_failed_when_mock_api_secret_missing(self):
        """测试缺少mock_api_secret时初始化失败"""
        previous_value = os.environ.get("MOCK_API_SECRET")
        os.environ["MOCK_API_SECRET"] = ""
        try:
            with self.assertRaises(ValueError):
                ConfigService()
        finally:
            if previous_value is None:
                os.environ.pop("MOCK_API_SECRET", None)
            else:
                os.environ["MOCK_API_SECRET"] = previous_value


if __name__ == "__main__":
    unittest.main()
