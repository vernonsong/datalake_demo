#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JSON工作流加载器
扫描skills/scenario-skill目录,加载所有JSON工作流
"""

import logging
from pathlib import Path
from typing import Dict

from app.workflows.langgraph_workflow_builder import LangGraphWorkflowBuilder
from app.workflows.registry import get_registry

logger = logging.getLogger(__name__)


def load_json_workflows():
    """加载所有JSON工作流"""
    logger.info("🔄 开始加载JSON工作流...")
    
    scenario_skill_dir = Path("skills/scenario-skill")
    
    if not scenario_skill_dir.exists():
        logger.warning(f"场景Skill目录不存在: {scenario_skill_dir}")
        return
    
    loaded_count = 0
    
    for skill_dir in scenario_skill_dir.iterdir():
        if not skill_dir.is_dir():
            continue
        
        workflow_json = skill_dir / "workflow.json"
        if not workflow_json.exists():
            continue
        
        try:
            builder = LangGraphWorkflowBuilder(str(skill_dir))
            workflow = builder.build()
            metadata = builder.get_metadata()
            
            workflow_name = metadata["name"]
            
            get_registry().register(
                name=workflow_name,
                workflow=workflow,
                metadata=metadata
            )
            
            loaded_count += 1
            logger.info(f"✅ 加载JSON工作流: {workflow_name} v{metadata['version']}")
            
        except Exception as e:
            logger.error(f"❌ 加载工作流失败 {skill_dir.name}: {e}", exc_info=True)
    
    logger.info(f"✅ JSON工作流加载完成,共加载 {loaded_count} 个工作流")
