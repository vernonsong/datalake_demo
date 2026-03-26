from typing import Optional, Dict, Any
import os


class ConfigSection:
    """配置节基类"""
    
    def __init__(self, config: Dict[str, Any], section_name: str):
        self._config = config
        self._section_name = section_name
    
    def _get(self, key: str, default: Any = None) -> Any:
        return self._config.get(self._section_name, {}).get(key, default)


class AppConfig(ConfigSection):
    """应用配置"""
    
    @property
    def name(self) -> str:
        return self._get("name")
    
    @property
    def version(self) -> str:
        return self._get("version")
    
    @property
    def debug(self) -> bool:
        return self._get("debug", False)


class ServerConfig(ConfigSection):
    """服务配置"""
    
    @property
    def host(self) -> str:
        return self._get("host")
    
    @property
    def port(self) -> int:
        return self._get("port")


class MockServiceConfig(ConfigSection):
    """Mock服务配置"""
    
    @property
    def url(self) -> str:
        return self._get("url")
    
    @property
    def api_secret(self) -> str:
        return self._get("api_secret")


class JwtConfig(ConfigSection):
    """JWT配置"""
    
    @property
    def secret(self) -> str:
        return self._get("secret")


class AliCloudConfig(ConfigSection):
    """阿里云配置"""
    
    @property
    def api_key(self) -> Optional[str]:
        return self._get("api_key")


class FileUploadConfig(ConfigSection):
    """文件上传配置"""
    
    @property
    def enabled(self) -> bool:
        return self._get("enabled", False)
    
    @property
    def max_size(self) -> int:
        return self._get("max_size")
    
    @property
    def allowed_extensions(self) -> list[str]:
        return self._get("allowed_extensions", [])
    
    @property
    def temp_dir(self) -> str:
        return self._get("temp_dir")
    
    @property
    def cleanup_hours(self) -> int:
        return self._get("cleanup_hours")


class Settings:
    """应用设置"""

    def __init__(self):
        from dotenv import load_dotenv
        load_dotenv()

        self._env = os.getenv("ENV")
        if not self._env:
            raise ValueError("ENV environment variable is required")

        self._config: Optional[Dict[str, Any]] = None
        self._app: Optional[AppConfig] = None
        self._server: Optional[ServerConfig] = None
        self._mock_service: Optional[MockServiceConfig] = None
        self._jwt: Optional[JwtConfig] = None
        self._ali_cloud: Optional[AliCloudConfig] = None
        self._file_upload: Optional[FileUploadConfig] = None

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
    def app(self) -> AppConfig:
        if self._app is None:
            self._app = AppConfig(self._load_config(), "app")
        return self._app

    @property
    def server(self) -> ServerConfig:
        if self._server is None:
            self._server = ServerConfig(self._load_config(), "server")
        return self._server

    @property
    def mock_service(self) -> MockServiceConfig:
        if self._mock_service is None:
            self._mock_service = MockServiceConfig(self._load_config(), "mock_service")
        return self._mock_service

    @property
    def jwt(self) -> JwtConfig:
        if self._jwt is None:
            self._jwt = JwtConfig(self._load_config(), "jwt")
        return self._jwt

    @property
    def ali_cloud(self) -> AliCloudConfig:
        if self._ali_cloud is None:
            self._ali_cloud = AliCloudConfig(self._load_config(), "ali_cloud")
        return self._ali_cloud

    @property
    def file_upload(self) -> FileUploadConfig:
        if self._file_upload is None:
            self._file_upload = FileUploadConfig(self._load_config(), "file_upload")
        return self._file_upload

    @property
    def app_name(self) -> str:
        return self.app.name

    @property
    def app_version(self) -> str:
        return self.app.version

    @property
    def debug(self) -> bool:
        return self.app.debug

    @property
    def host(self) -> str:
        return self.server.host

    @property
    def port(self) -> int:
        return self.server.port

    @property
    def mock_service_url(self) -> str:
        return self.mock_service.url

    @property
    def mock_api_secret(self) -> str:
        return self.mock_service.api_secret

    @property
    def jwt_secret(self) -> str:
        return self.jwt.secret

    @property
    def ali_api_key(self) -> Optional[str]:
        return self.ali_cloud.api_key

    @property
    def file_upload_enabled(self) -> bool:
        return self.file_upload.enabled

    @property
    def file_upload_max_size(self) -> int:
        return self.file_upload.max_size

    @property
    def file_upload_allowed_extensions(self) -> list[str]:
        return self.file_upload.allowed_extensions

    @property
    def file_upload_temp_dir(self) -> str:
        return self.file_upload.temp_dir

    @property
    def file_upload_cleanup_hours(self) -> int:
        return self.file_upload.cleanup_hours


settings = Settings()
