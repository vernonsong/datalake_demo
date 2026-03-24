from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from typing import Optional
from pydantic import BaseModel
from app.core.dependencies import get_chat_agent
from app.agents.chat_agent import ChatAgent
import json


router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    """聊天请求"""
    message: str
    user_id: Optional[str] = "default_user"
    conversation_id: Optional[str] = None
    stream: Optional[bool] = False


class ChatResponse(BaseModel):
    """聊天响应"""
    success: bool
    message: str
    conversation_id: Optional[str] = None
    workflow_json: Optional[dict] = None


def stream_generator(chat_agent: ChatAgent, user_id: str, message: str, conv_id: Optional[str] = None):
    """流式生成器 - 返回模型的每一步思考和行动"""
    try:
        # 使用流式接口获取模型的每一步输出
        for event in chat_agent.chat_stream(user_id=user_id, message=message, conv_id=conv_id):
            event_type = event.get('type', 'unknown')
            
            if event_type == 'token':
                # Token 级流式
                content = event.get('content', '')
                yield f"data: {json.dumps({'type': 'token', 'content': content}, ensure_ascii=False)}\n\n"
            
            elif event_type == 'message':
                # 完整 AI 消息
                role = event.get('role', 'assistant')
                content = event.get('content', '')
                yield f"data: {json.dumps({'type': 'message', 'role': role, 'content': content}, ensure_ascii=False)}\n\n"
            
            elif event_type == 'tool':
                # 工具调用结果
                tool_name = event.get('name', 'unknown')
                tool_content = event.get('content', '')
                yield f"data: {json.dumps({'type': 'tool', 'name': tool_name, 'content': tool_content}, ensure_ascii=False)}\n\n"
            
            elif event_type == 'tool_call':
                # 工具调用请求
                tool_name = event.get('name', 'unknown')
                tool_args = event.get('args', {})
                yield f"data: {json.dumps({'type': 'tool_call', 'name': tool_name, 'args': tool_args}, ensure_ascii=False)}\n\n"
            
            elif event_type == 'file_read':
                # 文件读取事件 - 只输出路径
                file_path = event.get('path', '')
                yield f"data: {json.dumps({'type': 'file_read', 'path': file_path}, ensure_ascii=False)}\n\n"
            
            elif event_type == 'todos':
                # Todo 列表更新
                todos = event.get('content', [])
                yield f"data: {json.dumps({'type': 'todos', 'content': todos}, ensure_ascii=False)}\n\n"

            elif event_type == 'phase':
                phase = event.get('phase', '')
                yield f"data: {json.dumps({'type': 'phase', 'phase': phase}, ensure_ascii=False)}\n\n"
            
            elif event_type == 'done':
                # 处理完成
                yield f"data: {json.dumps({'type': 'done', 'content': event.get('content', '处理完成')}, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"
            
            elif event_type == 'error':
                # 错误处理
                yield f"data: {json.dumps({'type': 'error', 'error': event.get('error', '未知错误')}, ensure_ascii=False)}\n\n"
        
    except Exception as e:
        # 错误处理
        import traceback
        error_detail = traceback.format_exc()
        yield f"data: {json.dumps({'type': 'error', 'error': str(e), 'detail': error_detail}, ensure_ascii=False)}\n\n"


@router.post("/")
def chat(
    request: ChatRequest,
    chat_agent: ChatAgent = Depends(get_chat_agent)
):
    """聊天接口（支持流式和非流式）"""
    if request.stream:
        # 流式返回
        return StreamingResponse(
            stream_generator(
                chat_agent=chat_agent,
                user_id=request.user_id,
                message=request.message,
                conv_id=request.conversation_id
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    else:
        # 非流式返回（兼容旧接口）
        result = chat_agent.chat(
            user_id=request.user_id,
            message=request.message,
            conv_id=request.conversation_id
        )
        return ChatResponse(**result)
