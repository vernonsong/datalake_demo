from typing import Optional, Dict, Any
import os


class Settings:
    """应用设置"""

    def __init__(self):
        from dotenv import load_dotenv
        load_dotenv()

        self._env = os.getenv("ENV")
        if not self._env:
            raise ValueError("ENV environment variable is required")

        self._config: Optional[Dict[str, Any]] = None

    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        if self._config is None:
            from app.config import get_config
            from app.core.dependencies import get_token
            
            first_pass_config = get_config(env=self._env)
            
            config_service_url = first_pass_config.get("mock_service", {}).get("url")
            config_service_token = get_token() if config_service_url else None
            
            if config_service_url:
                self._config = get_config(
                    env=self._env,
                    config_service_url=config_service_url,
                    config_service_token=config_service_token
                )
            else:
                self._config = first_pass_config
        return self._config

    @property
    def env(self) -> str:
        return self._env

    @property
    def app_name(self) -> str:
        config = self._load_config()
        return config.get("app", {}).get("name")

    @property
    def app_version(self) -> str:
        config = self._load_config()
        return config.get("app", {}).get("version")

    @property
    def debug(self) -> bool:
        config = self._load_config()
        return config.get("app", {}).get("debug", False)

    @property
    def host(self) -> str:
        config = self._load_config()
        return config.get("server", {}).get("host")

    @property
    def port(self) -> int:
        config = self._load_config()
        return config.get("server", {}).get("port")

    @property
    def mock_service_url(self) -> str:
        config = self._load_config()
        return config.get("mock_service", {}).get("url")

    @property
    def mock_api_secret(self) -> str:
        config = self._load_config()
        return config.get("mock_service", {}).get("api_secret")

    @property
    def jwt_secret(self) -> str:
        config = self._load_config()
        return config.get("jwt", {}).get("secret")

    @property
    def ali_api_key(self) -> Optional[str]:
        config = self._load_config()
        return config.get("ali_cloud", {}).get("api_key")

    @property
    def file_upload_enabled(self) -> bool:
        config = self._load_config()
        return config.get("file_upload", {}).get("enabled", False)

    @property
    def file_upload_max_size(self) -> int:
        config = self._load_config()
        return config.get("file_upload", {}).get("max_size")

    @property
    def file_upload_allowed_extensions(self) -> list[str]:
        config = self._load_config()
        return config.get("file_upload", {}).get("allowed_extensions", [])

    @property
    def file_upload_temp_dir(self) -> str:
        config = self._load_config()
        return config.get("file_upload", {}).get("temp_dir")

    @property
    def file_upload_cleanup_hours(self) -> int:
        config = self._load_config()
        return config.get("file_upload", {}).get("cleanup_hours")


settings = Settings()
