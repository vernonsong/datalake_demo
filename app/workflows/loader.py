#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流加载器
在应用启动时自动加载和注册所有工作流
"""

import logging

logger = logging.getLogger(__name__)


def load_all_workflows():
    """加载所有工作流
    
    加载JSON配置的工作流(新架构)
    """
    logger.info("🔄 开始加载工作流...")
    
    try:
        from app.workflows.json_workflow_loader import load_json_workflows
        
        load_json_workflows()
        
        logger.info("✅ 所有工作流加载完成")
        
        from app.workflows.registry import get_registry
        registry = get_registry()
        workflows = registry.list_workflows()
        logger.info(f"📋 已注册工作流: {', '.join(workflows)}")
        
    except Exception as e:
        logger.error(f"❌ 工作流加载失败: {e}", exc_info=True)
        raise
