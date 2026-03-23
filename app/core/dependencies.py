#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
依赖注入模块
提供客户端的依赖注入函数
"""

from functools import lru_cache
from deepagents import create_deep_agent
from deepagents.backends import LocalShellBackend

from app.config import get_config


class TokenProvider:
    """Token提供者"""

    def __init__(self):
        from app.settings import settings
        self.base_url = settings.mock_service_url
        self.secret = settings.mock_api_secret
        self._token = None

    def get_token(self) -> str:
        """获取Token"""
        if self._token:
            return self._token

        try:
            import requests
            response = requests.post(
                f"{self.base_url}/api/token",
                json={"secret": self.secret},
                timeout=5
            )
            if response.status_code == 200:
                self._token = response.json().get("token")
                return self._token or ""
        except Exception:
            pass
        return ""

    def clear_token(self):
        """清除Token缓存"""
        self._token = None


_token_provider: TokenProvider = None


def get_token_provider() -> TokenProvider:
    """获取Token提供者单例"""
    global _token_provider
    if _token_provider is None:
        _token_provider = TokenProvider()
    return _token_provider


def get_token() -> str:
    """获取Token的便捷函数"""
    return get_token_provider().get_token()


@lru_cache()
def get_app_config() -> dict:
    """获取应用配置"""
    return get_config()


@lru_cache()
def get_metadata_client():
    """获取元数据服务客户端（依赖注入）"""
    from app.core.clients.metadata_client import MetadataClient
    config = get_app_config()
    platform_config = config.get("platform", {}).get("metadata", {})
    base_url = platform_config.get("url")
    if not base_url:
        raise ValueError("platform.metadata.url is required in config")
    base_url = base_url.rsplit('/api/', 1)[0]
    return MetadataClient(
        base_url=base_url,
        token_provider=get_token
    )


@lru_cache()
def get_schedule_client():
    """获取调度服务客户端（依赖注入）"""
    from app.core.clients.schedule_client import ScheduleClient
    config = get_app_config()
    platform_config = config.get("platform", {}).get("schedule", {})
    base_url = platform_config.get("url")
    if not base_url:
        raise ValueError("platform.schedule.url is required in config")
    base_url = base_url.rsplit('/api/', 1)[0]
    return ScheduleClient(
        base_url=base_url,
        token_provider=get_token
    )


@lru_cache()
def get_integration_client():
    """获取集成服务客户端（依赖注入）"""
    from app.core.clients.integration_client import IntegrationClient
    config = get_app_config()
    platform_config = config.get("platform", {}).get("integration", {})
    base_url = platform_config.get("url")
    if not base_url:
        raise ValueError("platform.integration.url is required in config")
    base_url = base_url.rsplit('/api/', 1)[0]
    return IntegrationClient(
        base_url=base_url,
        token_provider=get_token
    )


@lru_cache()
def get_lake_service_client():
    """获取湖服务客户端（依赖注入）"""
    from app.core.clients.lake_service_client import LakeServiceClient
    from app.settings import settings
    base_url = f"http://{settings.host}:{settings.port}"
    return LakeServiceClient(
        base_url=base_url,
        token_provider=get_token
    )


def get_ali_api_key() -> str:
    """从配置中心获取阿里云API Key"""
    from app.config import ConfigServiceClient
    from app.settings import settings

    config_service = ConfigServiceClient(
        base_url=settings.mock_service_url,
        token=get_token()
    )

    api_key = config_service.get_value("ali_api_key") or settings.ali_api_key
    if not api_key:
        raise ValueError("ali_api_key is required in config center or env")
    return api_key


@lru_cache()
def get_llm():
    """获取语言模型（依赖注入）"""
    from app.core.llm.log_llm import LogLLM

    api_key = get_ali_api_key()

    return LogLLM(
        model="qwen3.5-plus",
        temperature=0.01,
        base_url="https://coding.dashscope.aliyuncs.com/v1",
        api_key=api_key
    )


@lru_cache()
def get_deep_agent():
    """获取 DeepAgent 智能体（依赖注入）"""
    from deepagents import create_deep_agent
    from langgraph.checkpoint.memory import MemorySaver
    from deepagents.backends import LocalShellBackend
    from pathlib import Path

    PROJECT_ROOT = Path(__file__).parent.parent.parent

    llm = get_llm()
    checkpointer = MemorySaver()

    from app.agents.tools.platform_tool import get_platform_tools
    platform_tools = get_platform_tools()

    from app.core.system_prompt import SYSTEM_PROMPT

    return create_deep_agent(
        model=llm,
        system_prompt=SYSTEM_PROMPT,
        backend=LocalShellBackend(root_dir=str(PROJECT_ROOT)),
        skills=[
            str(PROJECT_ROOT / "skills/business-skill"),
            str(PROJECT_ROOT / "skills/platform-skill"),
        ],
        tools=platform_tools,
        interrupt_on={
                "write_file": True,
                "read_file": False,
                "edit_file": False,
                "execute_command": False,
                "create_directory": False
            },
        checkpointer=checkpointer,
    )


@lru_cache()
def get_chat_agent():
    """获取聊天智能体（依赖注入）"""
    from app.agents.chat_agent import ChatAgent
    return ChatAgent()
