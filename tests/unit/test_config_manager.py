import os
import tempfile
import shutil
import pytest
from unittest.mock import Mock, patch
from app.config import ConfigManager, ConfigServiceClient


class TestConfigManager:
    """配置管理器测试"""

    @pytest.fixture
    def temp_config_dir(self):
        """创建临时配置目录"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def base_yaml_content(self):
        """基础配置内容"""
        return """
app:
  name: 测试应用
  version: 1.0.0
  debug: false

server:
  host: 0.0.0.0
  port: 8000

database:
  host: localhost
  port: 5432
"""

    @pytest.fixture
    def env_yaml_content(self):
        """环境特定配置内容"""
        return """
app:
  debug: true

database:
  host: dev-db.internal
  pool_size: 5
"""

    def test_yaml_config_loading(self, temp_config_dir, base_yaml_content):
        """测试点1: YAML配置读取"""
        base_file = os.path.join(temp_config_dir, "base.yaml")
        with open(base_file, 'w', encoding='utf-8') as f:
            f.write(base_yaml_content)

        manager = ConfigManager(
            config_dir=temp_config_dir,
            env="dev"
        )
        config = manager.load_config()

        assert config["app"]["name"] == "测试应用"
        assert config["app"]["version"] == "1.0.0"
        assert config["app"]["debug"] is False
        assert config["server"]["host"] == "0.0.0.0"
        assert config["server"]["port"] == 8000
        assert config["database"]["host"] == "localhost"
        assert config["database"]["port"] == 5432

    def test_multiple_yaml_merge(self, temp_config_dir, base_yaml_content, env_yaml_content):
        """测试点2: 多YAML配置合并"""
        base_file = os.path.join(temp_config_dir, "base.yaml")
        with open(base_file, 'w', encoding='utf-8') as f:
            f.write(base_yaml_content)

        env_file = os.path.join(temp_config_dir, "app-dev.yaml")
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(env_yaml_content)

        manager = ConfigManager(
            config_dir=temp_config_dir,
            env="dev"
        )
        config = manager.load_config()

        assert config["app"]["name"] == "测试应用"
        assert config["app"]["version"] == "1.0.0"
        assert config["app"]["debug"] is True
        assert config["database"]["host"] == "dev-db.internal"
        assert config["database"]["port"] == 5432
        assert config["database"]["pool_size"] == 5

    def test_environment_specific_loading(self, temp_config_dir):
        """测试点3: 不同环境YAML配置选装"""
        base_content = """
app:
  name: 测试应用
  env: base
"""
        dev_content = """
app:
  env: dev
  debug: true
"""
        sit_content = """
app:
  env: sit
  debug: false
"""

        with open(os.path.join(temp_config_dir, "base.yaml"), 'w', encoding='utf-8') as f:
            f.write(base_content)
        with open(os.path.join(temp_config_dir, "app-dev.yaml"), 'w', encoding='utf-8') as f:
            f.write(dev_content)
        with open(os.path.join(temp_config_dir, "app-sit.yaml"), 'w', encoding='utf-8') as f:
            f.write(sit_content)

        manager_dev = ConfigManager(config_dir=temp_config_dir, env="dev")
        config_dev = manager_dev.load_config()
        assert config_dev["app"]["env"] == "dev"
        assert config_dev["app"]["debug"] is True

        manager_sit = ConfigManager(config_dir=temp_config_dir, env="sit")
        config_sit = manager_sit.load_config()
        assert config_sit["app"]["env"] == "sit"
        assert config_sit["app"]["debug"] is False

    def test_config_service_placeholder_replacement(self, temp_config_dir):
        """测试点4: 从配置中心获取配置"""
        yaml_content = """
app:
  name: 测试应用

database:
  host: ${database.host}
  port: ${database.port}
  username: ${database.username}
  password: ${database.password}

api:
  key: ${api.key}
"""
        with open(os.path.join(temp_config_dir, "base.yaml"), 'w', encoding='utf-8') as f:
            f.write(yaml_content)

        mock_service = Mock(spec=ConfigServiceClient)
        mock_service.get_value.side_effect = lambda key: {
            "database.host": "remote-db.example.com",
            "database.port": "3306",
            "database.username": "admin",
            "database.password": "secret123",
            "api.key": "api-key-12345"
        }.get(key)

        manager = ConfigManager(
            config_dir=temp_config_dir,
            env="dev",
            config_service_url="http://config-service.example.com",
            config_service_token="test-token"
        )
        manager._config_service = mock_service

        config = manager.load_config()

        assert config["app"]["name"] == "测试应用"
        assert config["database"]["host"] == "remote-db.example.com"
        assert config["database"]["port"] == "3306"
        assert config["database"]["username"] == "admin"
        assert config["database"]["password"] == "secret123"
        assert config["api"]["key"] == "api-key-12345"

    def test_config_cache(self, temp_config_dir, base_yaml_content):
        """测试配置缓存"""
        base_file = os.path.join(temp_config_dir, "base.yaml")
        with open(base_file, 'w', encoding='utf-8') as f:
            f.write(base_yaml_content)

        manager = ConfigManager(config_dir=temp_config_dir, env="dev")
        
        config1 = manager.load_config()
        config2 = manager.load_config()
        
        assert config1 is config2

    def test_config_reload(self, temp_config_dir):
        """测试配置重新加载"""
        base_file = os.path.join(temp_config_dir, "base.yaml")
        
        with open(base_file, 'w', encoding='utf-8') as f:
            f.write("app:\n  version: 1.0.0\n")

        manager = ConfigManager(config_dir=temp_config_dir, env="dev")
        config1 = manager.load_config()
        assert config1["app"]["version"] == "1.0.0"

        with open(base_file, 'w', encoding='utf-8') as f:
            f.write("app:\n  version: 2.0.0\n")

        config2 = manager.reload()
        assert config2["app"]["version"] == "2.0.0"

    def test_deep_merge(self, temp_config_dir):
        """测试深度合并"""
        base_content = """
app:
  name: 测试应用
  features:
    feature1: true
    feature2: false
  nested:
    level1:
      level2:
        value: base
"""
        override_content = """
app:
  features:
    feature2: true
    feature3: true
  nested:
    level1:
      level2:
        value: override
        new_value: added
"""
        with open(os.path.join(temp_config_dir, "base.yaml"), 'w', encoding='utf-8') as f:
            f.write(base_content)
        with open(os.path.join(temp_config_dir, "app-dev.yaml"), 'w', encoding='utf-8') as f:
            f.write(override_content)

        manager = ConfigManager(config_dir=temp_config_dir, env="dev")
        config = manager.load_config()

        assert config["app"]["name"] == "测试应用"
        assert config["app"]["features"]["feature1"] is True
        assert config["app"]["features"]["feature2"] is True
        assert config["app"]["features"]["feature3"] is True
        assert config["app"]["nested"]["level1"]["level2"]["value"] == "override"
        assert config["app"]["nested"]["level1"]["level2"]["new_value"] == "added"

    def test_placeholder_without_config_service(self, temp_config_dir):
        """测试没有配置中心时占位符保持不变"""
        yaml_content = """
database:
  host: ${database.host}
  port: 5432
"""
        with open(os.path.join(temp_config_dir, "base.yaml"), 'w', encoding='utf-8') as f:
            f.write(yaml_content)

        manager = ConfigManager(config_dir=temp_config_dir, env="dev")
        config = manager.load_config()

        assert config["database"]["host"] == "${database.host}"
        assert config["database"]["port"] == 5432
