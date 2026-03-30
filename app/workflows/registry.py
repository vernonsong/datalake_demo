#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流注册中心
管理所有LangGraph工作流的注册和获取
"""

from typing import Dict, Callable, Optional, Any
import logging

logger = logging.getLogger(__name__)


class WorkflowRegistry:
    """工作流注册中心"""
    
    def __init__(self):
        self._workflows: Dict[str, Any] = {}
        self._metadata: Dict[str, dict] = {}
    
    def register(self, name: str, workflow: Any, metadata: Optional[dict] = None):
        """注册工作流
        
        Args:
            name: 工作流名称 (如 "field-mapping")
            workflow: 编译后的LangGraph工作流
            metadata: 工作流元数据 (描述、参数说明等)
        """
        self._workflows[name] = workflow
        self._metadata[name] = metadata or {}
        logger.info(f"✅ 工作流已注册: {name}")
    
    def get(self, name: str) -> Optional[Any]:
        """获取工作流
        
        Args:
            name: 工作流名称
            
        Returns:
            编译后的工作流,如果不存在返回None
        """
        return self._workflows.get(name)
    
    def get_metadata(self, name: str) -> dict:
        """获取工作流元数据
        
        Args:
            name: 工作流名称
            
        Returns:
            工作流元数据
        """
        return self._metadata.get(name, {})
    
    def list_workflows(self) -> list:
        """列出所有已注册的工作流名称"""
        return list(self._workflows.keys())
    
    def exists(self, name: str) -> bool:
        """检查工作流是否存在"""
        return name in self._workflows
    
    def unregister(self, name: str):
        """注销工作流"""
        if name in self._workflows:
            del self._workflows[name]
            del self._metadata[name]
            logger.info(f"工作流已注销: {name}")


_registry = WorkflowRegistry()


def get_registry() -> WorkflowRegistry:
    """获取全局工作流注册中心"""
    return _registry


def register_workflow(name: str, metadata: Optional[dict] = None):
    """装饰器: 注册工作流
    
    用法:
        @register_workflow("field-mapping", metadata={
            "description": "字段映射工作流",
            "params": ["source_db", "source_table", "target_db"]
        })
        def build_field_mapping_workflow():
            workflow = StateGraph(...)
            ...
            return workflow.compile()
    
    Args:
        name: 工作流名称
        metadata: 工作流元数据
    """
    def decorator(build_func: Callable):
        workflow = build_func()
        _registry.register(name, workflow, metadata)
        return build_func
    return decorator


def get_workflow(name: str) -> Optional[Any]:
    """获取工作流的便捷函数
    
    Args:
        name: 工作流名称
        
    Returns:
        编译后的工作流,如果不存在返回None
    """
    return _registry.get(name)
