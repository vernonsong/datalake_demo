#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
客户端模块单元测试
"""

import os
import sys
import unittest
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestBaseClientInit(unittest.TestCase):
    """测试BaseClient初始化"""

    def test_init_with_all_params(self):
        """测试完整参数初始化"""
        from app.core.clients.base_client import BaseClient

        def token_provider():
            return "test-token"

        client = BaseClient(
            base_url="http://localhost:5001",
            timeout=30,
            token_provider=token_provider
        )

        self.assertEqual(client.base_url, "http://localhost:5001")
        self.assertEqual(client.timeout, 30)
        self.assertEqual(client.token_provider(), "test-token")

    def test_init_without_token_provider(self):
        """测试无token_provider初始化"""
        from app.core.clients.base_client import BaseClient

        client = BaseClient(
            base_url="http://localhost:5001",
            timeout=30
        )

        self.assertEqual(client.base_url, "http://localhost:5001")
        self.assertIsNone(client.token_provider)

    def test_base_url_strip_slash(self):
        """测试base_url去除末尾斜杠"""
        from app.core.clients.base_client import BaseClient

        client = BaseClient(
            base_url="http://localhost:5001/",
        )

        self.assertEqual(client.base_url, "http://localhost:5001")


class TestBaseClientAuth(unittest.TestCase):
    """测试BaseClient认证"""

    def test_get_auth_headers_with_token(self):
        """测试获取认证头-有token"""
        from app.core.clients.base_client import BaseClient

        def token_provider():
            return "test-token"

        client = BaseClient(
            base_url="http://localhost:5001",
            token_provider=token_provider
        )

        headers = client._get_auth_headers()
        self.assertEqual(headers["Authorization"], "Bearer test-token")

    def test_get_auth_headers_without_token(self):
        """测试获取认证头-无token"""
        from app.core.clients.base_client import BaseClient

        def token_provider():
            return None

        client = BaseClient(
            base_url="http://localhost:5001",
            token_provider=token_provider
        )

        headers = client._get_auth_headers()
        self.assertEqual(headers, {})

    def test_get_auth_headers_without_provider(self):
        """测试获取认证头-无provider"""
        from app.core.clients.base_client import BaseClient

        client = BaseClient(
            base_url="http://localhost:5001"
        )

        headers = client._get_auth_headers()
        self.assertEqual(headers, {})


class TestMetadataClient(unittest.TestCase):
    """测试MetadataClient"""

    def test_init(self):
        """测试初始化"""
        from app.core.clients.metadata_client import MetadataClient

        client = MetadataClient(
            base_url="http://localhost:5001",
            token_provider=lambda: "token"
        )

        self.assertEqual(client.base_url, "http://localhost:5001")


class TestIntegrationClient(unittest.TestCase):
    """测试IntegrationClient"""

    def test_init(self):
        """测试初始化"""
        from app.core.clients.integration_client import IntegrationClient

        client = IntegrationClient(
            base_url="http://localhost:5001",
            token_provider=lambda: "token"
        )

        self.assertEqual(client.base_url, "http://localhost:5001")


class TestScheduleClient(unittest.TestCase):
    """测试ScheduleClient"""

    def test_init(self):
        """测试初始化"""
        from app.core.clients.schedule_client import ScheduleClient

        client = ScheduleClient(
            base_url="http://localhost:5001",
            token_provider=lambda: "token"
        )

        self.assertEqual(client.base_url, "http://localhost:5001")


class TestSqlExecutionClient(unittest.TestCase):
    """测试SqlExecutionClient"""

    def test_init(self):
        """测试初始化"""
        from app.core.clients.sql_execution_client import SqlExecutionClient

        client = SqlExecutionClient(
            base_url="http://localhost:5001",
            token_provider=lambda: "token"
        )

        self.assertEqual(client.base_url, "http://localhost:5001")


class TestLakeServiceClient(unittest.TestCase):
    """测试LakeServiceClient"""

    def test_init(self):
        """测试初始化"""
        from app.core.clients.lake_service_client import LakeServiceClient

        client = LakeServiceClient(
            base_url="http://localhost:8000",
            token_provider=lambda: "token"
        )

        self.assertEqual(client.base_url, "http://localhost:8000")


class TestDependencyInjection(unittest.TestCase):
    """测试依赖注入"""

    def test_token_provider(self):
        """测试Token提供者"""
        from app.core.dependencies import TokenProvider

        provider = TokenProvider()
        token = provider.get_token()
        self.assertIsNotNone(token)
        self.assertGreater(len(token), 0)

    def test_get_token(self):
        """测试获取Token函数"""
        from app.core.dependencies import get_token

        token = get_token()
        self.assertIsNotNone(token)
        self.assertGreater(len(token), 0)


class TestClientRequest(unittest.TestCase):
    """测试客户端请求"""

    @patch('requests.Session.request')
    def test_request_get_success(self, mock_request):
        """测试GET请求成功"""
        from app.core.clients.base_client import BaseClient

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        mock_request.return_value = mock_response

        client = BaseClient(
            base_url="http://localhost:5001",
            token_provider=lambda: "token"
        )

        result = client.request("GET", "/api/test")

        self.assertEqual(result, {"data": "test"})
        mock_request.assert_called_once()

    @patch('requests.Session.request')
    def test_request_post_with_json(self, mock_request):
        """测试POST请求带JSON"""
        from app.core.clients.base_client import BaseClient

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_request.return_value = mock_response

        client = BaseClient(
            base_url="http://localhost:5001",
            token_provider=lambda: "token"
        )

        result = client.request("POST", "/api/test", json={"key": "value"})

        self.assertEqual(result, {"success": True})

    @patch('requests.Session.request')
    def test_request_without_auth(self, mock_request):
        """测试不带认证的请求"""
        from app.core.clients.base_client import BaseClient

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "public"}
        mock_request.return_value = mock_response

        client = BaseClient(
            base_url="http://localhost:5001",
            token_provider=lambda: "token"
        )

        result = client.request("GET", "/health", use_auth=False)

        self.assertEqual(result, {"data": "public"})

    @patch('requests.Session.request')
    def test_request_http_error(self, mock_request):
        """测试HTTP错误"""
        from app.core.clients.base_client import BaseClient
        import requests

        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.HTTPError("Not Found")
        mock_request.return_value = mock_response

        client = BaseClient(
            base_url="http://localhost:5001",
            token_provider=lambda: "token"
        )

        result = client.request("GET", "/api/notfound")

        self.assertFalse(result["success"])
        self.assertIn("error", result)


if __name__ == "__main__":
    unittest.main()
