#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
依赖注入模块单元测试
"""

import os
import sys
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.core import dependencies


class TestAliApiKeyDependency(unittest.TestCase):
    """测试ali_api_key依赖注入"""

    def test_get_ali_api_key_success(self):
        """测试成功获取ali_api_key"""
        mock_client = Mock()
        mock_client.get_value.return_value = "test-ali-api-key"
        with patch("app.config.ConfigServiceClient", return_value=mock_client):
            with patch("app.core.dependencies.get_token", return_value="token"):
                result = dependencies.get_ali_api_key()
        self.assertEqual(result, "test-ali-api-key")

    def test_get_ali_api_key_missing(self):
        """测试ali_api_key缺失时报错"""
        from app.settings import settings
        mock_ali_cloud = Mock()
        mock_ali_cloud.api_key = None
        with patch.object(settings, '_ali_cloud', mock_ali_cloud):
            with patch("app.config.ConfigServiceClient") as mock_client_class:
                mock_client = Mock()
                mock_client.get_value.return_value = None
                mock_client_class.return_value = mock_client
                with self.assertRaises(ValueError):
                    dependencies.get_ali_api_key()

    def test_get_ali_api_key_fallback_to_env(self):
        """测试配置中心不可用时回退环境变量"""
        from app.settings import settings
        mock_ali_cloud = Mock()
        mock_ali_cloud.api_key = "env-ali-api-key"
        with patch.object(settings, '_ali_cloud', mock_ali_cloud):
            with patch("app.config.ConfigServiceClient") as mock_client_class:
                mock_client = Mock()
                mock_client.get_value.return_value = None
                mock_client_class.return_value = mock_client
                result = dependencies.get_ali_api_key()
        self.assertEqual(result, "env-ali-api-key")


class TestLlmDependency(unittest.TestCase):
    """测试LLM依赖注入"""

    def setUp(self):
        dependencies.get_llm.cache_clear()

    def tearDown(self):
        dependencies.get_llm.cache_clear()

    def test_get_llm_uses_config_center_key(self):
        """测试get_llm使用配置中心key"""
        mock_llm = Mock()
        with patch("app.core.dependencies.get_ali_api_key", return_value="from-config-center"):
            with patch("app.core.llm.log_llm.LogLLM", return_value=mock_llm) as mock_log_llm:
                result = dependencies.get_llm()
        self.assertIs(result, mock_llm)
        self.assertEqual(mock_log_llm.call_args.kwargs["api_key"], "from-config-center")


if __name__ == "__main__":
    unittest.main()
