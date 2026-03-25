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
        4. 批量处理进度（batch_progress）
        
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
            - {type: "batch_progress", data: {...}}  # 批量处理进度
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
            last_phase = None
            
            # 使用 stream_mode="messages" 获取 token 级流式
            # 同时使用 stream_mode="values" 获取状态快照（包含 todos）
            tool_call_buffer = {}  # 缓存工具调用 chunks
            last_state = None  # 保存最后的状态，用于检查中断
            
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
                    
                    # 检查消息类型，处理工具响应
                    msg_type = type(msg).__name__
                    if 'ToolMessage' in msg_type:
                        # 工具响应消息，检查是否包含批量处理进度
                        if hasattr(msg, 'content') and msg.content:
                            content_str = str(msg.content)
                            # 解析 [BATCH_PROGRESS] 标记
                            import re
                            progress_matches = re.findall(r'\[BATCH_PROGRESS\]\s*(\{.*?\})', content_str, re.DOTALL)
                            for progress_json in progress_matches:
                                try:
                                    progress_data = json.loads(progress_json)
                                    yield {
                                        'type': 'batch_progress',
                                        'data': progress_data
                                    }
                                except json.JSONDecodeError:
                                    pass
                        # 跳过工具响应的常规输出
                        continue
                    
                    # 处理工具调用 chunks
                    if hasattr(msg, 'tool_call_chunks') and msg.tool_call_chunks:
                        for tc_chunk in msg.tool_call_chunks:
                            idx = tc_chunk.get('index')
                            if idx is not None:
                                if idx not in tool_call_buffer:
                                    tool_call_buffer[idx] = {'name': '', 'args': '', 'id': '', 'type': 'tool_call'}
                                
                                if tc_chunk.get('name'):
                                    tool_call_buffer[idx]['name'] += tc_chunk['name']
                                if tc_chunk.get('args'):
                                    tool_call_buffer[idx]['args'] += tc_chunk['args']
                                if tc_chunk.get('id'):
                                    tool_call_buffer[idx]['id'] += tc_chunk['id']
                        continue

                    if hasattr(msg, 'content') and msg.content:
                        # 如果有文本内容，且有缓存的工具调用，说明工具调用已结束（或穿插），先发送工具调用
                        if tool_call_buffer:
                            for idx in sorted(tool_call_buffer.keys()):
                                tool_info = tool_call_buffer[idx]
                                # 尝试解析 args
                                try:
                                    if tool_info['args']:
                                        tool_info['args'] = json.loads(tool_info['args'])
                                except json.JSONDecodeError:
                                    pass # 保持原样或忽略
                                
                                # 发送工具调用事件
                                tool_name = tool_info['name']
                                tool_args = tool_info['args']
                                
                                # 1. 处理文件读取工具
                                if tool_name in ['read_file', 'read', 'file_read']:
                                    file_path = tool_args.get('file_path', tool_args.get('path', '')) if isinstance(tool_args, dict) else ''
                                    if file_path:
                                        import os
                                        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
                                        try:
                                            rel_path = os.path.relpath(file_path, project_root)
                                            yield {
                                                'type': 'file_read',
                                                'path': rel_path
                                            }
                                        except ValueError:
                                            yield {
                                                'type': 'file_read',
                                                'path': file_path
                                            }
                                # 2. 处理 Todo 列表更新工具 - 跳过
                                elif tool_name in ['write_todos', 'TodoWrite']:
                                    pass
                                else:
                                    yield {
                                        'type': 'tool_call',
                                        'name': tool_name,
                                        'args': tool_args
                                    }
                            tool_call_buffer.clear()

                        # 发送 token
                        yield {
                            'type': 'token',
                            'content': msg.content
                        }
                
                elif mode == "values":
                    # 状态快照 - 获取 todos 等信息
                    last_state = chunk  # 保存最后的状态
                    
                    # 先清空并发送缓存的工具调用（确保在状态更新前发送）
                    if tool_call_buffer:
                        for idx in sorted(tool_call_buffer.keys()):
                            tool_info = tool_call_buffer[idx]
                            try:
                                if tool_info['args']:
                                    tool_info['args'] = json.loads(tool_info['args'])
                            except json.JSONDecodeError:
                                pass
                            
                            tool_name = tool_info['name']
                            tool_args = tool_info['args']
                            
                            if tool_name in ['read_file', 'read', 'file_read']:
                                file_path = tool_args.get('file_path', tool_args.get('path', '')) if isinstance(tool_args, dict) else ''
                                if file_path:
                                    import os
                                    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
                                    try:
                                        rel_path = os.path.relpath(file_path, project_root)
                                        yield {'type': 'file_read', 'path': rel_path}
                                    except ValueError:
                                        yield {'type': 'file_read', 'path': file_path}
                            elif tool_name in ['write_todos', 'TodoWrite']:
                                pass
                            else:
                                yield {
                                    'type': 'tool_call',
                                    'name': tool_name,
                                    'args': tool_args
                                }
                        tool_call_buffer.clear()

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

                        if todos:
                            if any(t.get('status') in ['pending', 'in_progress'] for t in todos if isinstance(t, dict)):
                                phase = 'thinking'
                            elif all(t.get('status') == 'completed' for t in todos if isinstance(t, dict)):
                                phase = 'final'
                            else:
                                phase = None

                            if phase and phase != last_phase:
                                last_phase = phase
                                yield {
                                    'type': 'phase',
                                    'phase': phase
                                }
                        
                        # 注意：不再从 values 中提取 tool_calls 发送，因为已经在 messages 中处理了
                        # 避免重复发送

            
            # 发送剩余的工具调用
            if tool_call_buffer:
                for idx in sorted(tool_call_buffer.keys()):
                    tool_info = tool_call_buffer[idx]
                    try:
                        if tool_info['args']:
                            tool_info['args'] = json.loads(tool_info['args'])
                    except json.JSONDecodeError:
                        pass
                    
                    tool_name = tool_info['name']
                    tool_args = tool_info['args']
                    
                    if tool_name in ['read_file', 'read', 'file_read']:
                        file_path = tool_args.get('file_path', tool_args.get('path', '')) if isinstance(tool_args, dict) else ''
                        if file_path:
                            import os
                            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
                            try:
                                rel_path = os.path.relpath(file_path, project_root)
                                yield {'type': 'file_read', 'path': rel_path}
                            except ValueError:
                                yield {'type': 'file_read', 'path': file_path}
                    elif tool_name in ['write_todos', 'TodoWrite']:
                        pass
                    else:
                        yield {
                            'type': 'tool_call',
                            'name': tool_name,
                            'args': tool_args
                        }
                tool_call_buffer.clear()

            # 检查是否有中断
            if last_state and '__interrupt__' in last_state:
                interrupt_data = last_state['__interrupt__']
                logger.info(f"🛑 检测到中断: {interrupt_data}")
                logger.info(f"🛑 中断数据类型: {type(interrupt_data)}")
                
                # 将 Interrupt 对象转换为可序列化的格式
                try:
                    # 尝试将对象转换为字典
                    if isinstance(interrupt_data, list):
                        interrupt_info = []
                        for item in interrupt_data:
                            try:
                                # 尝试访问对象属性
                                interrupt_info.append({
                                    'value': str(getattr(item, 'value', item)),
                                    'resumable': bool(getattr(item, 'resumable', True)),
                                    'ns': list(getattr(item, 'ns', [])),
                                    'when': str(getattr(item, 'when', 'during'))
                                })
                            except Exception as e:
                                logger.error(f"转换中断项失败: {e}")
                                # 如果转换失败，使用字符串表示
                                interrupt_info.append({'value': str(item)})
                    else:
                        # 如果不是列表，直接转换为字符串
                        interrupt_info = [{'value': str(interrupt_data)}]
                except Exception as e:
                    logger.error(f"转换中断数据失败: {e}", exc_info=True)
                    interrupt_info = [{'value': 'Tool execution requires approval'}]
                
                # 发送中断事件给前端
                yield {
                    'type': 'interrupt',
                    'interrupt_info': interrupt_info,
                    'thread_id': thread_id
                }
            else:
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
