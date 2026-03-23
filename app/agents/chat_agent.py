#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对话服务 - 统一的对话接口
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from uuid import uuid4

logger = logging.getLogger(__name__)


class ChatAgent:
    """对话服务"""

    def __init__(self, llm=None, agent=None):
        """初始化对话服务

        Args:
            llm: 语言模型实例（可选，由依赖注入提供）
            agent: 智能体实例（可选，由依赖注入提供）
        """
        self._llm = llm
        self._agent = agent

    @property
    def llm(self):
        """获取语言模型"""
        if self._llm is None:
            from app.core.dependencies import get_llm
            self._llm = get_llm()
        return self._llm

    @property
    def agent(self):
        """获取智能体"""
        if self._agent is None:
            from app.core.dependencies import get_deep_agent
            self._agent = get_deep_agent()
        return self._agent

    def _resolve_thread_id(self, user_id: str, conv_id: Optional[str]) -> str:
        if conv_id:
            return conv_id
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
        return f"{user_id}_{timestamp}_{uuid4().hex[:8]}"

    def chat(self, user_id: str, message: str, conv_id: Optional[str] = None) -> Dict[str, Any]:
        """对话接口

        Args:
            user_id: 用户ID
            message: 用户消息
            conv_id: 会话ID（可选）

        Returns:
            对话响应
        """
        logger.info(f"💬 收到消息：{user_id} - {message[:100]}...")

        deepagents_messages = []
        deepagents_messages.append({"role": "user", "content": message})

        logger.info(f"🤖 DeepAgents智能体输入：\n{json.dumps(deepagents_messages, ensure_ascii=False, indent=2)}")

        thread_id = self._resolve_thread_id(user_id, conv_id)

        result = self.agent.invoke(
            {"messages": deepagents_messages},
            config={"configurable": {"thread_id": thread_id}},
        )

        logger.info(f"🤖 DeepAgents智能体输出类型：{type(result)}")

        response_message = ""
        if isinstance(result, dict):
            messages = result.get("messages", [])
            if messages:
                last_message = messages[-1]
                if hasattr(last_message, 'content'):
                    response_message = last_message.content
                elif isinstance(last_message, dict):
                    response_message = last_message.get("content", "")

        response = {
            'success': True,
            'message': response_message,
            'conversation_id': thread_id
        }

        workflow = result.get('workflow_json')
        if workflow:
            response['workflow_json'] = workflow

        return response

    def handle_message(self, message: str, conversation_id: Optional[str] = None) -> Dict[str, Any]:
        """处理消息（简化接口）"""
        return self.chat(
            user_id="default_user",
            message=message,
            conv_id=conversation_id
        )

    def chat_stream(self, user_id: str, message: str, conv_id: Optional[str] = None):
        """流式对话接口 - 同时返回 token 流、todos 和工具调用
        
        使用 LangGraph 的 stream API，支持：
        1. token 级流式文本（stream_mode="messages"）
        2. todo 列表状态更新
        3. 工具调用记录
        
        参考：https://docs.langchain.com/oss/python/deepagents/frontend/overview
        
        Args:
            user_id: 用户 ID
            message: 用户消息
            conv_id: 会话 ID
            
        Yields:
            流式事件，格式：
            - {type: "token", content: "单个 token 文本"}  # token 级流式
            - {type: "message", role: "assistant", content: "完整消息"}  # 完整 AI 消息
            - {type: "todos", content: [...]}  # todo 列表更新
            - {type: "tool_call", name: "工具名", args: {...}}  # 工具调用请求
            - {type: "file_read", path: "相对路径"}  # 文件读取事件
            - {type: "done", content: "完成"}
        """
        logger.info(f"💬 收到流式消息：{user_id} - {message[:100]}...")
        
        deepagents_messages = []
        deepagents_messages.append({"role": "user", "content": message})
        
        logger.info(f"🤖 DeepAgents 智能体输入：\n{json.dumps(deepagents_messages, ensure_ascii=False, indent=2)}")
        
        # 使用 LangGraph 的 stream API - 真正的流式
        try:
            thread_id = self._resolve_thread_id(user_id, conv_id)
            last_todos = None
            initial_todos_captured = False
            last_ai_content = ""
            
            # 使用 stream_mode="messages" 获取 token 级流式
            # 同时使用 stream_mode="values" 获取状态快照（包含 todos）
            for mode, chunk in self.agent.stream(
                {"messages": deepagents_messages},
                config={"configurable": {"thread_id": thread_id}},
                stream_mode=["messages", "values"],  # 同时获取 token 流和状态快照
            ):
                if mode == "messages":
                    # token 级流式 - chunk 是 (message, metadata) 元组
                    msg, metadata = chunk
                    
                    # 检查是否是工具响应（避免输出读取的文件内容）
                    if metadata and isinstance(metadata, dict):
                        node_name = metadata.get('langgraph_node', '')
                        # 如果是工具响应节点，跳过内容输出
                        if node_name in ['tool_responses', 'write_tool_response']:
                            continue
                    
                    # 检查消息类型，过滤工具响应
                    msg_type = type(msg).__name__
                    if 'ToolMessage' in msg_type:
                        # 工具响应消息，跳过不输出
                        continue
                    
                    if hasattr(msg, 'content') and msg.content:
                        # 发送 token
                        yield {
                            'type': 'token',
                            'content': msg.content
                        }
                
                elif mode == "values":
                    # 状态快照 - 获取 todos 等信息
                    if isinstance(chunk, dict):
                        # 检查 todos 状态
                        todos = chunk.get("todos", [])
                        if not initial_todos_captured:
                            last_todos = todos
                            initial_todos_captured = True
                        elif todos and todos != last_todos:
                            yield {
                                'type': 'todos',
                                'content': todos
                            }
                            last_todos = todos
                        
                        # 检查工具调用
                        messages = chunk.get("messages", [])
                        if messages:
                            msg = messages[-1]
                            
                            # 检查工具调用请求
                            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                                for tc in msg.tool_calls:
                                    tool_name = tc.get('name') if isinstance(tc, dict) else getattr(tc, 'name', 'unknown')
                                    tool_args = tc.get('args') if isinstance(tc, dict) else getattr(tc, 'args', {})
                                    
                                    # 处理特殊工具调用：只发送专用事件，不发送通用的 tool_call 事件
                                    
                                    # 1. 处理文件读取工具
                                    if tool_name in ['read_file', 'read', 'file_read']:
                                        file_path = tool_args.get('file_path', tool_args.get('path', ''))
                                        if file_path:
                                            # 转换为相对路径
                                            import os
                                            # 维持原有逻辑：项目根目录的上级目录，使路径包含项目文件夹名
                                            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
                                            try:
                                                rel_path = os.path.relpath(file_path, project_root)
                                                yield {
                                                    'type': 'file_read',
                                                    'path': rel_path
                                                }
                                            except ValueError:
                                                # 如果不在同一文件系统，使用原路径
                                                yield {
                                                    'type': 'file_read',
                                                    'path': file_path
                                                }
                                        continue # 跳过通用 tool_call
                                    
                                    # 2. 处理 Todo 列表更新工具
                                    if tool_name in ['write_todos', 'TodoWrite']:
                                        # Todo 列表会由上面的 mode == "values" 逻辑检测到状态变化并发送 todos 事件
                                        # 这里直接跳过通用的 tool_call 事件
                                        continue

                                    # 发送通用的工具调用事件
                                    yield {
                                        'type': 'tool_call',
                                        'name': tool_name,
                                        'args': tool_args
                                    }
            
            # 发送完成事件
            yield {
                'type': 'done',
                'content': '处理完成'
            }
            
        except Exception as e:
            logger.error(f"❌ 流式处理错误：{e}", exc_info=True)
            yield {
                'type': 'error',
                'error': str(e)
            }
