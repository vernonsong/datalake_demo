#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自定义DeepAgent创建函数
修改system_prompt处理逻辑：用户自定义提示词优先于框架默认提示词
"""

import os
from typing import Any, Callable, Sequence
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langchain_core.messages import SystemMessage
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.store.base import BaseStore
from langgraph.cache.base import BaseCache
from langgraph.prebuilt.tool_node import ToolRuntime
from deepagents.backends.protocol import BackendProtocol, BackendFactory
from deepagents.middleware.subagents import SubAgent, CompiledSubAgent


def _get_base_agent_prompt() -> str:
    """获取框架默认提示词"""
    import deepagents
    base_dir = os.path.dirname(deepagents.__file__)
    prompt_file = os.path.join(base_dir, 'base_prompt.md')
    with open(prompt_file, 'r', encoding='utf-8') as f:
        return f.read()


BASE_AGENT_PROMPT = _get_base_agent_prompt()


def create_my_deep_agent(
    model: str | BaseChatModel | None = None,
    tools: Sequence[BaseTool | Callable | dict[str, Any]] | None = None,
    *,
    system_prompt: str | SystemMessage | None = None,
    middleware: Sequence[Any] = (),
    subagents: list[SubAgent | CompiledSubAgent] | None = None,
    skills: list[str] | None = None,
    memory: list[str] | None = None,
    response_format: Any | None = None,
    context_schema: type[Any] | None = None,
    checkpointer: BaseCheckpointSaver | None = None,
    store: BaseStore | None = None,
    backend: BackendProtocol | Callable[[ToolRuntime], BackendProtocol] | None = None,
    interrupt_on: dict[str, bool | Any] | None = None,
    debug: bool = False,
    name: str | None = None,
    cache: BaseCache | None = None,
):
    """创建DeepAgent，用户自定义system_prompt优先，框架默认提示词放在后面"""
    
    from deepagents import create_deep_agent
    
    # 关键修改：用户自定义提示词在前，框架默认提示词在后
    if system_prompt is not None:
        if isinstance(system_prompt, SystemMessage):
            final_prompt = system_prompt + f"\n\n{BASE_AGENT_PROMPT}"
        else:
            final_prompt = system_prompt + "\n\n" + BASE_AGENT_PROMPT
    else:
        final_prompt = None
    
    return create_deep_agent(
        model=model,
        tools=tools,
        system_prompt=final_prompt,
        middleware=middleware,
        subagents=subagents,
        skills=skills,
        memory=memory,
        response_format=response_format,
        context_schema=context_schema,
        checkpointer=checkpointer,
        store=store,
        backend=backend,
        interrupt_on=interrupt_on,
        debug=debug,
        name=name,
        cache=cache,
    )
