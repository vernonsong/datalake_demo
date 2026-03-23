#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志LLM包装类 - 打印模型输入输出
"""

import json
from typing import Any, Dict, List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.callbacks import CallbackManagerForLLMRun


class LogLLM(ChatOpenAI):
    """日志LLM，打印模型输入输出"""

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        print("\n" + "=" * 80)
        print("🤖 [LLM INPUT]")
        print("=" * 80)
        for i, msg in enumerate(messages):
            role = msg.type.upper() if hasattr(msg, 'type') else "UNKNOWN"
            content = msg.content if hasattr(msg, 'content') else str(msg)
            print(f"\n--- Message {i+1} [{role}] ---")
            print(content[:2000] if len(content) > 2000 else content)
        print("\n" + "=" * 80)

        result = super()._generate(messages, stop, run_manager, **kwargs)

        print("\n" + "=" * 80)
        print("🤖 [LLM OUTPUT]")
        print("=" * 80)
        for i, generation in enumerate(result.generations):
            msg_text = generation.text if hasattr(generation, 'text') else str(generation)
            print(f"\n--- Generation {i+1} ---")
            print(msg_text[:2000] if len(msg_text) > 2000 else msg_text)
        print("\n" + "=" * 80 + "\n")

        return result
