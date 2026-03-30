#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流执行工具
为智能体提供调用LangGraph工作流的能力
"""

from langchain_core.tools import tool
from typing import Dict, Any
import logging
import json

logger = logging.getLogger(__name__)


def _progress_callback(progress_data: dict):
    """工作流进度回调函数
    
    通过print输出进度标记,让chat_agent能够捕获
    """
    import json
    progress_json = json.dumps(progress_data, ensure_ascii=False)
    print(f"[WORKFLOW_PROGRESS] {progress_json}")


@tool
def execute_workflow(workflow_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """执行工作流
    
    这是一个高效的工作流执行工具,用于替代智能体自主规划的多步骤流程。
    工作流是预定义的确定性流程,无需LLM推理,执行速度快、稳定性高。
    
    Args:
        workflow_name: 工作流名称,可选值:
            - "field-mapping": 字段映射工作流
        params: 工作流参数,根据不同工作流要求不同:
            - field-mapping 需要: order_id, source_db, source_table, target_db, target_table
    
    Returns:
        工作流执行结果,包含:
        - success: 是否成功
        - data: 结果数据
        - errors: 错误列表(如果有)
    
    Examples:
        >>> execute_workflow("field-mapping", {
        ...     "order_id": "ORDER001",
        ...     "source_db": "source_db",
        ...     "source_table": "orders",
        ...     "target_db": "clickhouse",
        ...     "target_table": "dw_orders"
        ... })
        {
            "success": True,
            "data": {
                "csv_file": "ORDER001.csv",
                "ddl_file": "ORDER001-ddl.sql",
                "ddl_content": "CREATE TABLE ..."
            }
        }
    """
    from app.workflows.registry import get_workflow, get_registry
    from app.workflows.base import set_progress_callback, clear_progress_callback
    
    logger.info(f"🚀 执行工作流: {workflow_name}")
    logger.info(f"📋 参数: {json.dumps(params, ensure_ascii=False, indent=2)}")
    
    set_progress_callback(_progress_callback)
    
    workflow = get_workflow(workflow_name)
    if not workflow:
        available = get_registry().list_workflows()
        error_msg = f"工作流 '{workflow_name}' 不存在。可用工作流: {', '.join(available)}"
        logger.error(f"❌ {error_msg}")
        return {
            "success": False,
            "error": error_msg,
            "data": None
        }
    
    try:
        result = workflow.invoke(params)
        
        errors = result.get("errors", [])
        if errors:
            logger.warning(f"⚠️ 工作流执行完成但有错误: {errors}")
            return {
                "success": False,
                "error": "; ".join(errors),
                "data": result
            }
        
        logger.info(f"✅ 工作流执行成功")
        logger.debug(f"结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        error_msg = f"工作流执行异常: {str(e)}"
        logger.error(f"❌ {error_msg}", exc_info=True)
        return {
            "success": False,
            "error": error_msg,
            "data": None
        }
    finally:
        clear_progress_callback()


@tool
def list_workflows() -> Dict[str, Any]:
    """列出所有可用的工作流
    
    Returns:
        包含所有工作流名称和元数据的字典
    
    Examples:
        >>> list_workflows()
        {
            "workflows": [
                {
                    "name": "field-mapping",
                    "description": "字段映射工作流",
                    "params": {...}
                }
            ]
        }
    """
    from app.workflows.registry import get_registry
    
    registry = get_registry()
    workflows = []
    
    for name in registry.list_workflows():
        metadata = registry.get_metadata(name)
        workflows.append({
            "name": name,
            **metadata
        })
    
    logger.info(f"📋 可用工作流数量: {len(workflows)}")
    return {"workflows": workflows}


def get_workflow_tools():
    """获取所有工作流相关工具"""
    return [execute_workflow, list_workflows]
