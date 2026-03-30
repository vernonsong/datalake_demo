#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流基类
提供工作流的通用功能和状态定义
"""

from typing import TypedDict, Annotated, Any, Dict, Callable, Optional
from operator import add
import logging
import json

logger = logging.getLogger(__name__)


_progress_callback: Optional[Callable[[dict], None]] = None


def set_progress_callback(callback: Callable[[dict], None]):
    """设置进度回调函数
    
    Args:
        callback: 进度回调函数,接收进度数据字典
    """
    global _progress_callback
    _progress_callback = callback


def clear_progress_callback():
    """清除进度回调函数"""
    global _progress_callback
    _progress_callback = None


def emit_progress(workflow_name: str, node_name: str, status: str, data: dict = None):
    """发送工作流进度事件
    
    Args:
        workflow_name: 工作流名称
        node_name: 节点名称
        status: 状态 (started/completed/failed)
        data: 附加数据
    """
    if _progress_callback:
        progress_data = {
            "workflow": workflow_name,
            "node": node_name,
            "status": status,
            "data": data or {}
        }
        try:
            _progress_callback(progress_data)
        except Exception as e:
            logger.error(f"进度回调失败: {e}", exc_info=True)


class BaseWorkflowState(TypedDict, total=False):
    """工作流基础状态
    
    所有工作流状态都应该继承此基类
    """
    errors: Annotated[list, add]
    warnings: Annotated[list, add]
    metadata: dict


class WorkflowResult:
    """工作流执行结果"""
    
    def __init__(self, success: bool, data: Any = None, errors: list = None, warnings: list = None):
        self.success = success
        self.data = data or {}
        self.errors = errors or []
        self.warnings = warnings or []
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "success": self.success,
            "data": self.data,
            "errors": self.errors,
            "warnings": self.warnings
        }
    
    def __repr__(self):
        status = "✅ 成功" if self.success else "❌ 失败"
        return f"WorkflowResult({status}, errors={len(self.errors)}, warnings={len(self.warnings)})"


def create_error_result(error_message: str) -> Dict[str, Any]:
    """创建错误结果
    
    Args:
        error_message: 错误信息
        
    Returns:
        错误结果字典
    """
    return {
        "success": False,
        "error": error_message,
        "data": None
    }


def create_success_result(data: Any = None, message: str = None) -> Dict[str, Any]:
    """创建成功结果
    
    Args:
        data: 结果数据
        message: 成功信息
        
    Returns:
        成功结果字典
    """
    result = {
        "success": True,
        "data": data or {}
    }
    if message:
        result["message"] = message
    return result


def log_node_entry(node_name: str, state: dict):
    """记录节点进入日志
    
    Args:
        node_name: 节点名称
        state: 当前状态
    """
    logger.info(f"🔵 进入节点: {node_name}")
    logger.debug(f"当前状态: {state}")


def log_node_exit(node_name: str, updates: dict):
    """记录节点退出日志
    
    Args:
        node_name: 节点名称
        updates: 状态更新
    """
    logger.info(f"🟢 退出节点: {node_name}")
    logger.debug(f"状态更新: {updates}")


def log_node_error(node_name: str, error: Exception):
    """记录节点错误日志
    
    Args:
        node_name: 节点名称
        error: 异常对象
    """
    logger.error(f"🔴 节点错误: {node_name} - {str(error)}", exc_info=True)
