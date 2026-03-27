#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastAPI应用单元测试
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.main import app
from app.settings import settings


class TestAppRoot(unittest.TestCase):
    """测试根路径"""

    def setUp(self):
        self.client = TestClient(app)

    def test_root_returns_running(self):
        """测试根路径返回running状态"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["service"], settings.app.name)
        self.assertEqual(data["version"], settings.app.version)
        self.assertEqual(data["status"], "running")


class TestAppHealth(unittest.TestCase):
    """测试心跳接口"""

    def setUp(self):
        self.client = TestClient(app)

    def test_health_returns_healthy(self):
        """测试心跳接口返回healthy"""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("timestamp", data)
        self.assertIn("service", data)


class TestAppConfig(unittest.TestCase):
    """测试配置模块"""

    def test_settings_has_app_name(self):
        """测试配置有app_name"""
        self.assertEqual(settings.app.name, "智能入湖平台")

    def test_settings_has_version(self):
        """测试配置有版本号"""
        self.assertEqual(settings.app.version, "0.1.0")

    def test_settings_has_mock_service_url(self):
        """测试配置有mock服务地址"""
        self.assertIn("localhost", settings.mock_service.url)

    def test_settings_debug_default(self):
        """测试debug默认为True"""
        self.assertTrue(settings.app.debug)


class TestAppSchemas(unittest.TestCase):
    """测试数据模型"""

    def test_health_response_schema(self):
        """测试心跳响应模型"""
        from app.schemas import HealthResponse
        response = HealthResponse(
            status="healthy",
            timestamp="2024-01-01T00:00:00",
            service="test"
        )
        self.assertEqual(response.status, "healthy")
        self.assertEqual(response.timestamp, "2024-01-01T00:00:00")
        self.assertEqual(response.service, "test")

    def test_root_response_schema(self):
        """测试根路径响应模型"""
        from app.schemas import RootResponse
        response = RootResponse(
            service="test",
            version="1.0.0",
            status="running"
        )
        self.assertEqual(response.service, "test")
        self.assertEqual(response.version, "1.0.0")
        self.assertEqual(response.status, "running")


class TestAppRouter(unittest.TestCase):
    """测试路由模块"""

    def test_router_has_root_endpoint(self):
        """测试路由有根端点"""
        from app.routers import router
        routes = [r.path for r in router.routes]
        self.assertIn("/", routes)

    def test_router_has_health_endpoint(self):
        """测试路由有心跳端点"""
        from app.routers import router
        routes = [r.path for r in router.routes]
        self.assertIn("/health", routes)


class TestAppLifespan(unittest.TestCase):
    """测试生命周期模块"""

    def test_lifespan_exists(self):
        """测试lifespan存在"""
        from app.core import lifespan
        self.assertIsNotNone(lifespan)


if __name__ == "__main__":
    unittest.main()
