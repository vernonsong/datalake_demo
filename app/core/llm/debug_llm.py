#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试用LLM - 继承ChatOpenAI，打印输入输出
"""

import json
from typing import Any, Dict, List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage
from langchain_core.callbacks import CallbackManagerForLLMRun


class DebugLLM(ChatOpenAI):
    """调试用LLM，打印模型输入输出"""

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        print("\n" + "=" * 60)
        print("🤖 [LLM INPUT]")
        print("=" * 60)
        for msg in messages:
            print(f"\n--- {msg.type.upper()} ---")
            print(msg.content)
        print("\n" + "=" * 60)

        result = super()._generate(messages, stop, run_manager, **kwargs)

        print("\n" + "=" * 60)
        print("🤖 [LLM OUTPUT]")
        print("=" * 60)
        for generation in result.generations[0]:
            msg_type = getattr(generation, 'type', None) or 'unknown'
            msg_text = getattr(generation, 'text', None) or str(generation)
            print(f"\n--- {msg_type} ---")
            print(msg_text)
        print("\n" + "=" * 60 + "\n")

        return result


def get_llm():
    """获取调试用LLM"""
    from app.config import ConfigServiceClient
    from app.settings import settings
    from app.core.dependencies import get_token

    config_service = ConfigServiceClient(
        base_url=settings.mock_service.url,
        token=get_token()
    )

    api_key = config_service.get_value("ali_api_key")
    if not api_key:
        raise ValueError("ali_api_key is required in config center")

    return DebugLLM(
        model="qwen3.5-plus",
        temperature=0.3,
        base_url="https://coding.dashscope.aliyuncs.com/v1",
        api_key=api_key
    )
