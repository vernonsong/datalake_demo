import os
import re
from typing import Dict, Any, Optional, List
import yaml


class ConfigServiceClient:
    """配置中心客户端"""

    def __init__(self, base_url: str, token: str = None):
        self.base_url = base_url
        self.token = token

    def get_value(self, key: str) -> Optional[str]:
        """获取配置值"""
        try:
            import requests
            headers = {}
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"
            response = requests.get(
                f"{self.base_url}/api/config/{key}",
                headers=headers,
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                if "value" in data:
                    return data["value"]
        except Exception:
            pass
        return None


class ConfigManager:
    """配置管理器"""

    PLACEHOLDER_PATTERN = re.compile(r'\$\{([^}]+)\}')

    def __init__(
        self,
        config_dir: str,
        env: str,
        config_service_url: Optional[str] = None,
        config_service_token: Optional[str] = None
    ):
        """初始化配置管理器

        Args:
            config_dir: 配置目录路径
            env: 环境名称 (dev/sit/prod)
            config_service_url: 配置中心服务URL
            config_service_token: 配置中心服务Token
        """
        self.config_dir = config_dir
        self.env = env
        self.config_service_url = config_service_url
        self.config_service_token = config_service_token
        self._config_service: Optional[ConfigServiceClient] = None
        self._config_cache: Optional[Dict] = None

    @property
    def config_service(self) -> Optional[ConfigServiceClient]:
        """获取配置中心客户端"""
        if self.config_service_url and not self._config_service:
            self._config_service = ConfigServiceClient(
                self.config_service_url,
                token=self.config_service_token
            )
        return self._config_service

    def load_config(self) -> Dict[str, Any]:
        """加载并合并配置"""
        if self._config_cache is not None:
            return self._config_cache

        files = self._get_matching_files()
        configs = []
        for filename in files:
            config = self._load_yaml(filename)
            if config:
                configs.append(config)

        merged = self._merge_configs(configs)
        final = self._replace_placeholders(merged)

        self._config_cache = final
        return final

    def reload(self) -> Dict[str, Any]:
        """重新加载配置"""
        self._config_cache = None
        return self.load_config()

    def _get_matching_files(self) -> List[str]:
        """获取匹配当前环境的配置文件列表"""
        if not os.path.isdir(self.config_dir):
            return []

        matching_files = []
        all_files = []

        for filename in os.listdir(self.config_dir):
            if not filename.endswith('.yaml'):
                continue
            filepath = os.path.join(self.config_dir, filename)
            if os.path.isfile(filepath):
                all_files.append(filename)

        for filename in all_files:
            if '-' not in filename:
                matching_files.append(filename)
            else:
                file_env = filename.rsplit('-', 1)[1].replace('.yaml', '')
                if file_env == self.env:
                    matching_files.append(filename)

        matching_files.sort(key=lambda f: (
            '-' in f,
            f.rsplit('-', 1)[0] if '-' in f else f,
            f
        ))

        return matching_files

    def _load_yaml(self, filename: str) -> Dict[str, Any]:
        """加载单个YAML文件"""
        filepath = os.path.join(self.config_dir, filename)
        if not os.path.isfile(filepath):
            return {}

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                return data or {}
        except Exception:
            return {}

    def _merge_configs(self, configs: List[Dict]) -> Dict[str, Any]:
        """合并多个配置"""
        result = {}
        for config in configs:
            result = self._deep_merge(result, config)
        return result

    def _deep_merge(self, base: Dict, override: Dict) -> Dict:
        """深度合并两个字典"""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    def _replace_placeholders(self, config: Any) -> Any:
        """替换占位符"""
        if isinstance(config, dict):
            return {k: self._replace_placeholders(v) for k, v in config.items()}
        elif isinstance(config, list):
            return [self._replace_placeholders(item) for item in config]
        elif isinstance(config, str):
            return self._replace_string_placeholders(config)
        return config

    def _replace_string_placeholders(self, value: str) -> str:
        """替换字符串中的占位符"""
        matches = self.PLACEHOLDER_PATTERN.findall(value)

        if not matches:
            return value

        if self.config_service is None:
            return value

        for key in matches:
            config_value = self.config_service.get_value(key)
            if config_value is not None:
                value = value.replace(f'${{{key}}}', str(config_value))

        return value


def get_config(
    config_dir: str = None,
    env: str = None,
    config_service_url: str = None,
    config_service_token: str = None
) -> Dict[str, Any]:
    """获取配置的便捷函数

    Args:
        config_dir: 配置目录路径
        env: 环境名称
        config_service_url: 配置中心URL
        config_service_token: 配置中心Token

    Returns:
        配置字典
    """
    if config_dir is None:
        config_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config")

    if env is None:
        env = os.getenv("ENV", "dev")

    config_manager = ConfigManager(
        config_dir=config_dir,
        env=env,
        config_service_url=config_service_url,
        config_service_token=config_service_token
    )
    return config_manager.load_config()
