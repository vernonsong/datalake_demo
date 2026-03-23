#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置模块单元测试
"""

import os
import sys
import unittest
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import ConfigManager, ConfigServiceClient


class TestConfigServiceClient(unittest.TestCase):
    """测试配置中心客户端"""

    def test_client_init(self):
        """测试客户端初始化"""
        client = ConfigServiceClient("http://localhost:5001")
        self.assertEqual(client.base_url, "http://localhost:5001")

    def test_client_get_value_returns_none_when_no_service(self):
        """测试获取配置值-无服务时返回None"""
        client = ConfigServiceClient("http://localhost:5999")
        result = client.get_value("test_key")
        self.assertIsNone(result)


class TestConfigManagerInit(unittest.TestCase):
    """测试ConfigManager初始化"""

    def test_init_with_all_params(self):
        """测试完整参数初始化"""
        manager = ConfigManager(
            config_dir="/path/to/config",
            env="dev",
            config_service_url="http://localhost:5001"
        )
        self.assertEqual(manager.config_dir, "/path/to/config")
        self.assertEqual(manager.env, "dev")
        self.assertEqual(manager.config_service_url, "http://localhost:5001")

    def test_init_without_config_service(self):
        """测试无配置中心初始化"""
        manager = ConfigManager(
            config_dir="/path/to/config",
            env="dev"
        )
        self.assertEqual(manager.config_dir, "/path/to/config")
        self.assertEqual(manager.env, "dev")
        self.assertIsNone(manager.config_service_url)


class TestGetMatchingFiles(unittest.TestCase):
    """测试获取匹配文件"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config_files = {
            "base.yaml": "app:\n  name: test",
            "inter.yaml": "app:\n  env: inter",
            "inter-dev.yaml": "app:\n  debug: true",
            "inter-sit.yaml": "app:\n  debug: false",
            "prod.yaml": "app:\n  env: prod",
            "prod-prod.yaml": "app:\n  prod: true",
            "test.yaml": "app:\n  test: true",
        }
        for filename, content in self.config_files.items():
            filepath = os.path.join(self.temp_dir, filename)
            with open(filepath, 'w') as f:
                f.write(content)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_get_matching_files_dev(self):
        """测试dev环境匹配文件"""
        manager = ConfigManager(self.temp_dir, "dev")
        files = manager._get_matching_files()
        self.assertIn("base.yaml", files)
        self.assertIn("inter.yaml", files)
        self.assertIn("inter-dev.yaml", files)
        self.assertIn("prod.yaml", files)
        self.assertIn("test.yaml", files)
        self.assertNotIn("inter-sit.yaml", files)
        self.assertNotIn("prod-prod.yaml", files)

    def test_get_matching_files_sit(self):
        """测试sit环境匹配文件"""
        manager = ConfigManager(self.temp_dir, "sit")
        files = manager._get_matching_files()
        self.assertIn("base.yaml", files)
        self.assertIn("inter.yaml", files)
        self.assertIn("inter-sit.yaml", files)
        self.assertIn("prod.yaml", files)
        self.assertIn("test.yaml", files)
        self.assertNotIn("inter-dev.yaml", files)
        self.assertNotIn("prod-prod.yaml", files)

    def test_get_matching_files_prod(self):
        """测试prod环境匹配文件"""
        manager = ConfigManager(self.temp_dir, "prod")
        files = manager._get_matching_files()
        self.assertIn("base.yaml", files)
        self.assertIn("inter.yaml", files)
        self.assertIn("prod.yaml", files)
        self.assertIn("prod-prod.yaml", files)
        self.assertIn("test.yaml", files)
        self.assertNotIn("inter-dev.yaml", files)
        self.assertNotIn("inter-sit.yaml", files)

    def test_get_matching_files_empty_dir(self):
        """测试空目录"""
        empty_dir = tempfile.mkdtemp()
        try:
            manager = ConfigManager(empty_dir, "dev")
            files = manager._get_matching_files()
            self.assertEqual(files, [])
        finally:
            shutil.rmtree(empty_dir)

    def test_get_matching_files_nonexistent_dir(self):
        """测试不存在的目录"""
        manager = ConfigManager("/nonexistent/path", "dev")
        files = manager._get_matching_files()
        self.assertEqual(files, [])


class TestLoadYaml(unittest.TestCase):
    """测试YAML加载"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_load_existing_file(self):
        """测试加载存在的文件"""
        filepath = os.path.join(self.temp_dir, "test.yaml")
        with open(filepath, 'w') as f:
            f.write("app:\n  name: test\n  version: 1.0")

        manager = ConfigManager(self.temp_dir, "dev")
        config = manager._load_yaml("test.yaml")

        self.assertEqual(config["app"]["name"], "test")
        self.assertEqual(config["app"]["version"], 1.0)

    def test_load_nonexistent_file(self):
        """测试加载不存在的文件"""
        manager = ConfigManager(self.temp_dir, "dev")
        config = manager._load_yaml("nonexistent.yaml")
        self.assertEqual(config, {})

    def test_load_invalid_yaml(self):
        """测试加载无效YAML"""
        filepath = os.path.join(self.temp_dir, "invalid.yaml")
        with open(filepath, 'w') as f:
            f.write("invalid: yaml: content:")

        manager = ConfigManager(self.temp_dir, "dev")
        config = manager._load_yaml("invalid.yaml")
        self.assertEqual(config, {})


class TestMergeConfigs(unittest.TestCase):
    """测试配置合并"""

    def test_merge_simple_configs(self):
        """测试简单合并"""
        manager = ConfigManager("/tmp", "dev")

        config1 = {"a": 1, "b": 2}
        config2 = {"b": 3, "c": 4}
        result = manager._merge_configs([config1, config2])

        self.assertEqual(result["a"], 1)
        self.assertEqual(result["b"], 3)
        self.assertEqual(result["c"], 4)

    def test_merge_nested_configs(self):
        """测试嵌套合并"""
        manager = ConfigManager("/tmp", "dev")

        config1 = {"app": {"name": "test", "version": "1.0"}}
        config2 = {"app": {"version": "2.0", "debug": True}}
        result = manager._merge_configs([config1, config2])

        self.assertEqual(result["app"]["name"], "test")
        self.assertEqual(result["app"]["version"], "2.0")
        self.assertEqual(result["app"]["debug"], True)

    def test_merge_empty_list(self):
        """测试空列表合并"""
        manager = ConfigManager("/tmp", "dev")
        result = manager._merge_configs([])
        self.assertEqual(result, {})

    def test_merge_priority_later_overrides_earlier(self):
        """测试后配置优先"""
        manager = ConfigManager("/tmp", "dev")

        config1 = {"database": {"host": "localhost", "port": 3306}}
        config2 = {"database": {"host": "remote"}}
        result = manager._merge_configs([config1, config2])

        self.assertEqual(result["database"]["host"], "remote")
        self.assertEqual(result["database"]["port"], 3306)


class TestPlaceholderReplacement(unittest.TestCase):
    """测试占位符替换"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_replace_simple_placeholder(self):
        """测试简单占位符替换"""
        manager = ConfigManager(
            self.temp_dir,
            "dev",
            config_service_url="http://localhost:5999"
        )

        class MockConfigService:
            def get_value(self, key):
                if key == "app.name":
                    return "test-app"
                return None

        manager._config_service = MockConfigService()

        config = {"app": {"name": "${app.name}"}}
        result = manager._replace_placeholders(config)

        self.assertEqual(result["app"]["name"], "test-app")

    def test_replace_multiple_placeholders(self):
        """测试多个占位符"""
        manager = ConfigManager(
            self.temp_dir,
            "dev",
            config_service_url="http://localhost:5999"
        )

        class MockConfigService:
            def get_value(self, key):
                mapping = {
                    "database.host": "localhost",
                    "database.port": "3306"
                }
                return mapping.get(key)

        manager._config_service = MockConfigService()

        config = {
            "database": {
                "host": "${database.host}",
                "port": "${database.port}"
            }
        }
        result = manager._replace_placeholders(config)

        self.assertEqual(result["database"]["host"], "localhost")
        self.assertEqual(result["database"]["port"], "3306")

    def test_replace_no_placeholder(self):
        """测试无占位符"""
        manager = ConfigManager(self.temp_dir, "dev")

        config = {"app": {"name": "test"}}
        result = manager._replace_placeholders(config)

        self.assertEqual(result["app"]["name"], "test")

    def test_replace_nested_placeholders(self):
        """测试嵌套结构中的占位符"""
        manager = ConfigManager(
            self.temp_dir,
            "dev",
            config_service_url="http://localhost:5999"
        )

        class MockConfigService:
            def get_value(self, key):
                if key == "db.host":
                    return "db.internal"
                return None

        manager._config_service = MockConfigService()

        config = {
            "level1": {
                "level2": {
                    "host": "${db.host}"
                }
            }
        }
        result = manager._replace_placeholders(config)

        self.assertEqual(result["level1"]["level2"]["host"], "db.internal")

    def test_replace_placeholder_not_found(self):
        """测试占位符未找到"""
        manager = ConfigManager(
            self.temp_dir,
            "dev",
            config_service_url="http://localhost:5999"
        )

        class MockConfigService:
            def get_value(self, key):
                return None

        manager._config_service = MockConfigService()

        config = {"app": {"name": "${not.found}"}}
        result = manager._replace_placeholders(config)

        self.assertEqual(result["app"]["name"], "${not.found}")

    def test_replace_with_list(self):
        """测试列表中的占位符"""
        manager = ConfigManager(
            self.temp_dir,
            "dev",
            config_service_url="http://localhost:5999"
        )

        class MockConfigService:
            def get_value(self, key):
                if key == "items":
                    return "replaced"
                return None

        manager._config_service = MockConfigService()

        config = {"items": ["${items}", "normal"]}
        result = manager._replace_placeholders(config)

        self.assertEqual(result["items"][0], "replaced")
        self.assertEqual(result["items"][1], "normal")

    def test_replace_without_config_service(self):
        """测试无配置中心时保留占位符"""
        manager = ConfigManager(self.temp_dir, "dev")

        config = {"app": {"name": "${app.name}"}}
        result = manager._replace_placeholders(config)

        self.assertEqual(result["app"]["name"], "${app.name}")


class TestLoadConfigIntegration(unittest.TestCase):
    """测试配置加载集成"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        configs = {
            "base.yaml": """app:
  name: 智能入湖平台
  version: 0.1.0
database:
  host: ${database.host}
  port: ${database.port}
""",
            "inter.yaml": """app:
  env: inter
database:
  host: inter-db.internal
""",
            "inter-dev.yaml": """app:
  debug: true
database:
  host: inter-dev-db.internal
  pool_size: 5
"""
        }
        for filename, content in configs.items():
            filepath = os.path.join(self.temp_dir, filename)
            with open(filepath, 'w') as f:
                f.write(content)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_load_config_dev(self):
        """测试加载dev配置"""
        manager = ConfigManager(self.temp_dir, "dev")
        config = manager.load_config()

        self.assertEqual(config["app"]["name"], "智能入湖平台")
        self.assertEqual(config["app"]["version"], "0.1.0")
        self.assertEqual(config["app"]["env"], "inter")
        self.assertEqual(config["app"]["debug"], True)
        self.assertEqual(config["database"]["host"], "inter-dev-db.internal")
        self.assertEqual(config["database"]["port"], "${database.port}")
        self.assertEqual(config["database"]["pool_size"], 5)

    def test_load_config_cached(self):
        """测试配置缓存"""
        manager = ConfigManager(self.temp_dir, "dev")
        config1 = manager.load_config()
        config2 = manager.load_config()

        self.assertIs(config1, config2)

    def test_reload_config(self):
        """测试重新加载配置"""
        manager = ConfigManager(self.temp_dir, "dev")
        config1 = manager.load_config()
        config2 = manager.reload()

        self.assertEqual(config1, config2)
        self.assertIsNot(config1, config2)


class TestEdgeCases(unittest.TestCase):
    """边界测试"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_only_yaml_files(self):
        """测试只处理yaml文件"""
        open(os.path.join(self.temp_dir, "test.txt"), 'w').write("text")
        open(os.path.join(self.temp_dir, "test.json"), 'w').write("{}")

        manager = ConfigManager(self.temp_dir, "dev")
        files = manager._get_matching_files()

        self.assertEqual(files, [])

    def test_deeply_nested_merge(self):
        """测试深度嵌套合并"""
        manager = ConfigManager(self.temp_dir, "dev")

        config1 = {"a": {"b": {"c": 1}}}
        config2 = {"a": {"b": {"d": 2}}}
        result = manager._deep_merge(config1, config2)

        self.assertEqual(result["a"]["b"]["c"], 1)
        self.assertEqual(result["a"]["b"]["d"], 2)

    def test_special_characters_in_value(self):
        """测试特殊字符值"""
        manager = ConfigManager(
            self.temp_dir,
            "dev",
            config_service_url="http://localhost:5999"
        )

        class MockConfigService:
            def get_value(self, key):
                return "value-with-special:chars"

        manager._config_service = MockConfigService()

        config = {"app": {"name": "${app.name}"}}
        result = manager._replace_placeholders(config)

        self.assertEqual(result["app"]["name"], "value-with-special:chars")


if __name__ == "__main__":
    unittest.main()
