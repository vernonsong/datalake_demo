from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os


class AppSettings:
    """应用配置"""
    APP_NAME: str
    APP_VERSION: str
    DEBUG: bool
    ENV: str


class ServerSettings:
    """服务配置"""
    HOST: str
    PORT: int


class MockServiceSettings:
    """Mock服务配置"""
    MOCK_SERVICE_URL: str
    MOCK_API_SECRET: str


class JwtSettings:
    """JWT配置"""
    JWT_SECRET: str


class AliCloudSettings:
    """阿里云配置"""
    ALI_API_KEY: Optional[str] = None


class Settings:
    """应用设置"""

    def __init__(self):
        from dotenv import load_dotenv
        load_dotenv()

        self.app = AppSettings()
        self.app.APP_NAME = os.getenv("APP_NAME")
        self.app.APP_VERSION = os.getenv("APP_VERSION")
        debug_str = os.getenv("DEBUG")
        self.app.DEBUG = debug_str.lower() == "true" if debug_str else False
        self.app.ENV = os.getenv("ENV")

        self.server = ServerSettings()
        self.server.HOST = os.getenv("HOST")
        self.server.PORT = int(os.getenv("PORT"))

        self.mock_service = MockServiceSettings()
        self.mock_service.MOCK_SERVICE_URL = os.getenv("MOCK_SERVICE_URL")
        self.mock_service.MOCK_API_SECRET = os.getenv("MOCK_API_SECRET")

        self.jwt = JwtSettings()
        self.jwt.JWT_SECRET = os.getenv("JWT_SECRET")

        self.ali_cloud = AliCloudSettings()
        self.ali_cloud.ALI_API_KEY = os.getenv("ALI_API_KEY")

    @property
    def app_name(self) -> str:
        return self.app.APP_NAME

    @property
    def app_version(self) -> str:
        return self.app.APP_VERSION

    @property
    def debug(self) -> bool:
        return self.app.DEBUG

    @property
    def env(self) -> str:
        return self.app.ENV

    @property
    def host(self) -> str:
        return self.server.HOST

    @property
    def port(self) -> int:
        return self.server.PORT

    @property
    def mock_service_url(self) -> str:
        return self.mock_service.MOCK_SERVICE_URL

    @property
    def mock_api_secret(self) -> str:
        return self.mock_service.MOCK_API_SECRET

    @property
    def jwt_secret(self) -> str:
        return self.jwt.JWT_SECRET

    @property
    def ali_api_key(self) -> Optional[str]:
        return self.ali_cloud.ALI_API_KEY


settings = Settings()
