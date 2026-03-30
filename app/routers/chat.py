from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from typing import Optional, List
from pydantic import BaseModel
from app.core.dependencies import get_chat_agent
from app.agents.chat_agent import ChatAgent
from app.utils.file_validator import FileValidator
from app.utils.file_storage import FileStorage
from app.settings import settings
from pathlib import Path
import json
import logging
import shutil

logger = logging.getLogger(__name__)


class ResumeRequest(BaseModel):
    """恢复中断执行的请求"""
    thread_id: str
    decision: str  # "approve" 或 "reject"


router = APIRouter(prefix="/chat", tags=["chat"])

file_validator = FileValidator(
    allowed_extensions=settings.file_upload_allowed_extensions,
    max_file_size=settings.file_upload_max_size
)

file_storage = FileStorage(
    temp_dir=settings.file_upload_temp_dir,
    cleanup_after_hours=settings.file_upload_cleanup_hours
)


class ChatRequest(BaseModel):
    """聊天请求"""
    message: str
    user_id: Optional[str] = "default_user"
    conversation_id: Optional[str] = None
    stream: Optional[bool] = False


class UploadedFileInfo(BaseModel):
    """上传文件信息"""
    original_name: str
    file_id: str
    size: int
    type: str


class ChatResponse(BaseModel):
    """聊天响应"""
    success: bool
    message: str
    conversation_id: Optional[str] = None
    workflow_json: Optional[dict] = None
    uploaded_files: Optional[List[UploadedFileInfo]] = None


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
            
            elif event_type == 'batch_progress':
                # 批量处理进度
                progress_data = event.get('data', {})
                yield f"data: {json.dumps({'type': 'batch_progress', 'data': progress_data}, ensure_ascii=False)}\n\n"
            
            elif event_type == 'interrupt':
                # 中断事件 - 需要用户确认
                interrupt_info = event.get('interrupt_info', {})
                thread_id = event.get('thread_id', '')
                yield f"data: {json.dumps({'type': 'interrupt', 'interrupt_info': interrupt_info, 'thread_id': thread_id}, ensure_ascii=False)}\n\n"
            
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
async def chat(
    message: str = Form(...),
    user_id: Optional[str] = Form("default_user"),
    conversation_id: Optional[str] = Form(None),
    stream: Optional[bool] = Form(False),
    files: Optional[List[UploadFile]] = File(None),
    chat_agent: ChatAgent = Depends(get_chat_agent)
):
    """聊天接口（支持流式和非流式，支持文件上传）"""
    
    uploaded_files_info = []
    
    if files and settings.file_upload.enabled:
        if len(files) > 5:
            raise HTTPException(status_code=400, detail="单次最多上传5个文件")
        
        for file in files:
            is_valid, error = await file_validator.validate(file)
            if not is_valid:
                raise HTTPException(status_code=400, detail=f"文件验证失败: {error}")
            
            try:
                file_id, file_path, file_size = await file_storage.save_file(file)
                
                ext = Path(file.filename).suffix.lower()
                file_type = "excel" if ext in ['.xlsx', '.xls'] else "csv"
                
                uploaded_files_info.append(UploadedFileInfo(
                    original_name=file.filename,
                    file_id=file_id,
                    size=file_size,
                    type=file_type
                ))
                
                logger.info(f"文件上传成功: {file.filename} ({file_size} bytes)")
            
            except Exception as e:
                logger.error(f"文件保存失败: {e}")
                raise HTTPException(status_code=500, detail=f"文件保存失败: {str(e)}")
        
        if uploaded_files_info:
            file_info_text = "\n".join([
                f"- {f.original_name} ({f.type}, {f.size} bytes, ID: {f.file_id})"
                for f in uploaded_files_info
            ])
            message = f"{message}\n\n[已上传文件]\n{file_info_text}"
    
    if stream:
        return StreamingResponse(
            stream_generator(
                chat_agent=chat_agent,
                user_id=user_id,
                message=message,
                conv_id=conversation_id
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    else:
        result = chat_agent.chat(
            user_id=user_id,
            message=message,
            conv_id=conversation_id
        )
        
        if uploaded_files_info:
            result['uploaded_files'] = [f.model_dump() for f in uploaded_files_info]
        
        return ChatResponse(**result)


@router.post("/resume")
async def resume_execution(
    request: ResumeRequest,
    chat_agent: ChatAgent = Depends(get_chat_agent)
):
    """恢复中断的执行
    
    当用户确认或拒绝操作后，调用此接口恢复执行
    """
    try:
        from langgraph.types import Command
        
        logger.info(f"📤 恢复执行: thread_id={request.thread_id}, decision={request.decision}")
        
        # 使用 Command 恢复执行
        result = chat_agent.agent.invoke(
            Command(resume=request.decision),
            config={"configurable": {"thread_id": request.thread_id}}
        )
        
        # 提取最后的 AI 消息
        messages = result.get("messages", [])
        if messages:
            last_message = messages[-1]
            content = last_message.content if hasattr(last_message, 'content') else str(last_message)
            
            return {
                "success": True,
                "message": content,
                "thread_id": request.thread_id
            }
        else:
            return {
                "success": True,
                "message": "操作已处理",
                "thread_id": request.thread_id
            }
            
    except Exception as e:
        logger.error(f"❌ 恢复执行失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"恢复执行失败: {str(e)}")
