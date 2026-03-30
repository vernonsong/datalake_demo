#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
依赖注入模块
提供客户端的依赖注入函数
"""

from functools import lru_cache
from pathlib import Path
import re
import logging
from deepagents import create_deep_agent
from deepagents.backends import LocalShellBackend
from langchain.agents.middleware.human_in_the_loop import HumanInTheLoopMiddleware, InterruptOnConfig
from langchain_core.messages import AIMessage

from app.config import get_config

logger = logging.getLogger(__name__)


class DynamicHumanInTheLoopMiddleware(HumanInTheLoopMiddleware):
    """支持动态判断逻辑的 HumanInTheLoopMiddleware"""
    
    def __init__(self, interrupt_on: dict, dynamic_conditions: dict):
        super().__init__(interrupt_on=interrupt_on)
        self.dynamic_conditions = dynamic_conditions

    def after_model(self, state, runtime):
        logger.info(f"[DynamicHITL] after_model 被调用")
        
        # 检查是否有需要动态中断的工具调用
        messages = state["messages"]
        if not messages:
            logger.info(f"[DynamicHITL] 没有消息，跳过")
            return None
            
        last_ai_msg = next((msg for msg in reversed(messages) if isinstance(msg, AIMessage)), None)
        if not last_ai_msg or not last_ai_msg.tool_calls:
            logger.info(f"[DynamicHITL] 没有工具调用，跳过")
            return None

        logger.info(f"[DynamicHITL] 发现 {len(last_ai_msg.tool_calls)} 个工具调用")

        # 动态更新 interrupt_on 配置
        current_interrupt_on = self.interrupt_on.copy()
        
        for tool_call in last_ai_msg.tool_calls:
            tool_name = tool_call["name"]
            logger.info(f"[DynamicHITL] 检查工具调用: {tool_name}, args: {tool_call.get('args', {})}")
            
            if tool_name in self.dynamic_conditions:
                condition_func = self.dynamic_conditions[tool_name]
                try:
                    should_interrupt = condition_func(tool_call)
                    logger.info(f"[DynamicHITL] {tool_name} 动态判断结果: {should_interrupt}")
                    
                    if should_interrupt:
                        # 如果条件满足，添加中断配置
                        self.interrupt_on[tool_name] = InterruptOnConfig(
                            allowed_decisions=["approve", "reject"]
                        )
                        logger.info(f"[DynamicHITL] ✅ 已添加 {tool_name} 到中断配置")
                except Exception as e:
                    logger.error(f"动态中断判断失败: {e}", exc_info=True)
            else:
                logger.debug(f"[DynamicHITL] {tool_name} 不在动态条件中")
        
        try:
            # 调用父类逻辑
            logger.info(f"[DynamicHITL] 当前 interrupt_on 配置: {list(self.interrupt_on.keys())}")
            logger.info(f"[DynamicHITL] 调用父类 after_model")
            result = super().after_model(state, runtime)
            logger.info(f"[DynamicHITL] 父类 after_model 返回: {result}")
            return result
        finally:
            # 恢复配置
            self.interrupt_on = current_interrupt_on
            logger.info(f"[DynamicHITL] 已恢复 interrupt_on 配置")


class TokenProvider:
    """Token提供者"""

    def __init__(self):
        self._token = None
        self._expires_at = None
        self._base_url = None
        self._secret = None

    def _ensure_config(self):
        """延迟加载配置"""
        if self._base_url is None or self._secret is None:
            from app.config import get_config
            import os
            env = os.getenv("ENV", "dev")
            config = get_config(env=env)
            self._base_url = config.get("mock_service", {}).get("url")
            self._secret = config.get("mock_service", {}).get("api_secret")

    def get_token(self) -> str:
        """获取Token"""
        if self._token and self._expires_at:
            import time
            if time.time() < (self._expires_at - 30):
                return self._token
        elif self._token and not self._expires_at:
            return self._token

        self._ensure_config()
        
        if not self._base_url or not self._secret:
            return ""

        try:
            import requests
            response = requests.post(
                f"{self._base_url}/api/token",
                json={"secret": self._secret},
                timeout=5
            )
            if response.status_code == 200:
                payload = response.json() or {}
                self._token = payload.get("token")
                expires_in = payload.get("expires_in")
                if isinstance(expires_in, (int, float)):
                    import time
                    self._expires_at = time.time() + float(expires_in)
                return self._token or ""
        except Exception:
            pass
        return ""

    def clear_token(self):
        """清除Token缓存"""
        self._token = None
        self._expires_at = None


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
        token_provider=get_token_provider().get_token
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
        token_provider=get_token_provider().get_token
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
        token_provider=get_token_provider().get_token
    )


@lru_cache()
def get_sql_execution_client():
    """获取SQL执行服务客户端（依赖注入）"""
    from app.core.clients.sql_execution_client import SqlExecutionClient
    config = get_app_config()
    platform_config = config.get("platform", {}).get("sql", {})
    base_url = platform_config.get("url")
    if not base_url:
        raise ValueError("platform.sql.url is required in config")
    base_url = base_url.rsplit('/api/', 1)[0]
    return SqlExecutionClient(
        base_url=base_url,
        token_provider=get_token_provider().get_token
    )


@lru_cache()
def get_lake_service_client():
    """获取湖服务客户端（依赖注入）"""
    from app.core.clients.lake_service_client import LakeServiceClient
    from app.settings import settings
    base_url = f"http://{settings.server.host}:{settings.server.port}"
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

    api_key = config_service.get_value("ali_api_key") or settings.ali_cloud.api_key
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


def _resolve_doc_path(doc_path: str) -> Path:
    """解析文档路径
    
    Args:
        doc_path: 文档相对路径或绝对路径
    
    Returns:
        解析后的Path对象
    
    Raises:
        FileNotFoundError: 文档不存在
    """
    PROJECT_ROOT = Path(__file__).parent.parent.parent
    
    if doc_path.startswith('/'):
        resolved = Path(doc_path)
    else:
        resolved = PROJECT_ROOT / doc_path
    
    if not resolved.exists():
        raise FileNotFoundError(f"接口文档不存在: {resolved}")
    
    return resolved


def _should_interrupt_platform_service(tool_call: dict) -> bool:
    """判断platform_service调用是否需要中断
    
    通过读取接口文档中的REQUIRES_CONFIRMATION标记来判断
    
    Args:
        tool_call: 工具调用信息，包含args等
    
    Returns:
        True: 需要中断（需要用户确认）
        False: 不需要中断（不需要确认）
    """
    args = tool_call.get("args", {})
    doc_path = args.get("doc_path", "")
    
    if not doc_path:
        logger.warning("platform_service调用缺少doc_path参数")
        return False
    
    try:
        resolved_path = _resolve_doc_path(doc_path)
        
        content = resolved_path.read_text(encoding="utf-8")
        
        match = re.search(r'REQUIRES_CONFIRMATION:\s*(true|false)', content, re.IGNORECASE)
        
        if match:
            requires_confirmation = match.group(1).lower() == 'true'
            logger.info(f"接口文档 {doc_path} REQUIRES_CONFIRMATION={requires_confirmation}")
            return requires_confirmation
        else:
            logger.debug(f"接口文档 {doc_path} 未找到REQUIRES_CONFIRMATION标记，默认不需要确认")
            return False
    
    except Exception as e:
        logger.warning(f"读取接口文档失败: {doc_path}, 错误: {e}, 为安全起见默认需要确认")
        return True


# @lru_cache()  # 临时禁用缓存，以便测试中断功能
def get_deep_agent():
    """获取 DeepAgent 智能体（依赖注入）"""
    from deepagents import create_deep_agent
    from langgraph.checkpoint.memory import MemorySaver
    from deepagents.backends import LocalShellBackend
    from pathlib import Path

    PROJECT_ROOT = Path(__file__).parent.parent.parent

    llm = get_llm()
    checkpointer = MemorySaver()

    from app.workflows.loader import load_all_workflows
    load_all_workflows()
    
    from app.agents.tools.platform_tool import get_platform_tools
    from app.agents.tools.batch_tool import get_batch_tools
    from app.agents.tools.workflow_tool import get_workflow_tools
    
    platform_tools = get_platform_tools()
    batch_tools = get_batch_tools()
    workflow_tools = get_workflow_tools()

    from app.core.system_prompt import SYSTEM_PROMPT
    from app.core.subagents import ALL_SUBAGENTS

    # 静态中断配置
    static_interrupt_on = {
        "write_file": True,
        "read_file": False,
        "edit_file": False,
        "execute_command": False,
        "create_directory": False,
    }
    
    # 动态中断条件
    dynamic_conditions = {
        "platform_service": _should_interrupt_platform_service
    }
    
    # 创建动态中间件
    dynamic_middleware = DynamicHumanInTheLoopMiddleware(
        interrupt_on=static_interrupt_on,
        dynamic_conditions=dynamic_conditions
    )

    return create_deep_agent(
        model=llm,
        system_prompt=SYSTEM_PROMPT,
        backend=LocalShellBackend(root_dir=str(PROJECT_ROOT)),
        skills=[
            str(PROJECT_ROOT / "skills/business-skill"),
            str(PROJECT_ROOT / "skills/platform-skill"),
        ],
        tools=platform_tools + batch_tools + workflow_tools,
        subagents=ALL_SUBAGENTS,  # 注册子 Agent
        interrupt_on=None,  # 不使用内置的 HumanInTheLoopMiddleware
        middleware=[dynamic_middleware],  # 使用自定义的动态中间件
        checkpointer=checkpointer,
    )


@lru_cache()
def get_chat_agent():
    """获取聊天智能体（依赖注入）"""
    from app.agents.chat_agent import ChatAgent
    return ChatAgent()
