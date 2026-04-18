import json
from pathlib import Path
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

_workflow_cache: Dict[str, Dict[str, Any]] = {}


def load_all_workflows() -> None:
    """加载所有工作流定义到缓存"""
    workflow_dir = Path("workflows/definitions")
    
    if not workflow_dir.exists():
        logger.warning(f"工作流定义目录不存在: {workflow_dir}")
        return
    
    for workflow_file in workflow_dir.glob("*.json"):
        try:
            workflow_name = workflow_file.stem
            with open(workflow_file, "r", encoding="utf-8") as f:
                workflow_json = json.load(f)
            
            validate_workflow_definition(workflow_json)
            _workflow_cache[workflow_name] = workflow_json
            logger.info(f"已加载工作流: {workflow_name}")
        except Exception as e:
            logger.error(f"加载工作流 {workflow_file} 失败: {e}")


def get_all_workflow_names() -> List[str]:
    """获取所有已加载的工作流名称"""
    return list(_workflow_cache.keys())


def get_workflow_from_cache(workflow_name: str) -> Dict[str, Any]:
    """从缓存获取工作流定义"""
    if workflow_name not in _workflow_cache:
        raise FileNotFoundError(f"工作流未找到: {workflow_name}")
    return _workflow_cache[workflow_name]


def load_workflow_definition(workflow_name: str) -> Dict[str, Any]:
    workflow_path = Path("workflows/definitions") / f"{workflow_name}.json"
    
    if not workflow_path.exists():
        raise FileNotFoundError(f"工作流定义文件不存在: {workflow_path}")
    
    with open(workflow_path, "r", encoding="utf-8") as f:
        workflow_json = json.load(f)
    
    validate_workflow_definition(workflow_json)
    
    return workflow_json


def validate_workflow_definition(workflow_json: Dict[str, Any]) -> None:
    required_fields = ["nodes", "edges"]
    for field in required_fields:
        if field not in workflow_json:
            raise ValueError(f"工作流定义缺少必需字段: {field}")
    
    if not isinstance(workflow_json["nodes"], list):
        raise ValueError("nodes字段必须是数组")
    
    if not isinstance(workflow_json["edges"], list):
        raise ValueError("edges字段必须是数组")
    
    for node in workflow_json["nodes"]:
        if "id" not in node:
            raise ValueError("节点缺少id字段")
        if "type" not in node:
            raise ValueError(f"节点{node['id']}缺少type字段")
        if "config" not in node:
            raise ValueError(f"节点{node['id']}缺少config字段")
    
    for edge in workflow_json["edges"]:
        if "from" not in edge or "to" not in edge:
            raise ValueError("边缺少from或to字段")
