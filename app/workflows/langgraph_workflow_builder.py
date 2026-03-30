#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LangGraph工作流构建器
从JSON配置构建LangGraph工作流,支持条件边、工具调用、人工审批
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, List, Callable
import logging

from langgraph.graph import StateGraph, END

from app.workflows.base import emit_progress

logger = logging.getLogger(__name__)


class LangGraphWorkflowBuilder:
    """LangGraph工作流构建器"""
    
    def __init__(self, workflow_dir: str):
        """初始化构建器
        
        Args:
            workflow_dir: 工作流目录路径
        """
        self.workflow_dir = Path(workflow_dir)
        self.config_file = self.workflow_dir / "workflow.json"
        self.config = self._load_config()
        self.tools = self._load_tools()
        
    def _load_config(self) -> dict:
        """加载工作流配置"""
        if not self.config_file.exists():
            raise FileNotFoundError(f"工作流配置文件不存在: {self.config_file}")
        
        with open(self.config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        logger.info(f"✅ 加载工作流配置: {config['name']} v{config['version']}")
        return config
    
    def _load_tools(self) -> Dict[str, Callable]:
        """加载可用工具"""
        from app.agents.tools.platform_tool import platform_service
        
        return {
            "platform_service": platform_service
        }
    
    def build(self):
        """构建LangGraph工作流"""
        state_class = self._create_state_class()
        
        graph = StateGraph(state_class)
        
        nodes_map = {node["id"]: node for node in self.config["nodes"]}
        
        for node in self.config["nodes"]:
            node_func = self._create_node_function(node)
            graph.add_node(node["id"], node_func)
        
        entry_point = self.config.get("entry_point")
        if entry_point:
            graph.set_entry_point(entry_point)
        
        # 按from_node分组边
        edges_by_source = {}
        for edge in self.config["edges"]:
            from_node = edge["from"]
            if from_node not in edges_by_source:
                edges_by_source[from_node] = []
            edges_by_source[from_node].append(edge)
        
        # 处理每个节点的边
        for from_node, edges in edges_by_source.items():
            # 分离normal边和conditional边
            normal_edges = [e for e in edges if e.get("type", "normal") == "normal"]
            conditional_edges = [e for e in edges if e.get("type") == "conditional"]
            
            # 添加normal边
            for edge in normal_edges:
                graph.add_edge(from_node, edge["to"])
            
            # 添加conditional边(合并为一个条件函数)
            if conditional_edges:
                # 创建路由函数
                def create_router(cond_edges):
                    def router(state):
                        for edge in cond_edges:
                            condition = edge["condition"]
                            field = condition["field"]
                            operator = condition["operator"]
                            value = condition["value"]
                            state_value = state.get(field)
                            
                            matched = False
                            if operator == "==":
                                matched = state_value == value
                            elif operator == "!=":
                                matched = state_value != value
                            elif operator == ">":
                                matched = state_value > value
                            elif operator == "<":
                                matched = state_value < value
                            elif operator == ">=":
                                matched = state_value >= value
                            elif operator == "<=":
                                matched = state_value <= value
                            elif operator == "in":
                                matched = state_value in value
                            elif operator == "not in":
                                matched = state_value not in value
                            
                            if matched:
                                to_node = edge["to"]
                                return END if to_node == "__end__" else to_node
                        
                        # 默认返回END
                        return END
                    return router
                
                router_func = create_router(conditional_edges)
                # 构建路径映射
                path_map = {}
                for edge in conditional_edges:
                    to_node = edge["to"]
                    if to_node == "__end__":
                        path_map[END] = END
                    else:
                        path_map[to_node] = to_node
                
                graph.add_conditional_edges(
                    from_node,
                    router_func,
                    path_map
                )
        
        logger.info(f"✅ LangGraph工作流构建完成: {self.config['name']}")
        return graph.compile()
    
    def _create_state_class(self):
        """动态创建状态类
        
        使用简单的dict作为状态,LangGraph支持dict作为状态
        """
        return dict
    
    def _create_node_function(self, node: dict) -> Callable:
        """创建节点函数"""
        node_id = node["id"]
        node_type = node.get("type", "script")
        workflow_name = self.config["name"]
        
        if node_type == "script":
            return self._create_script_node(node_id, node, workflow_name)
        elif node_type == "tool":
            return self._create_tool_node(node_id, node, workflow_name)
        elif node_type == "human":
            return self._create_human_node(node_id, node, workflow_name)
        else:
            raise ValueError(f"不支持的节点类型: {node_type}")
    
    def _create_script_node(self, node_id: str, node: dict, workflow_name: str) -> Callable:
        """创建脚本节点"""
        script_path = self.workflow_dir / node["script"]
        
        def script_node(state: dict) -> dict:
            emit_progress(workflow_name, node_id, "started", {
                "description": node["progress"]["started"]
            })
            
            try:
                inputs = {key: state.get(key) for key in node.get("inputs", [])}
                
                result = self._run_script(script_path, inputs)
                
                if not result.get("success"):
                    error_msg = result.get("error", "未知错误")
                    emit_progress(workflow_name, node_id, "failed", {
                        "description": node["progress"]["failed"],
                        "error": error_msg
                    })
                    return {"errors": [f"{node['name']}失败: {error_msg}"]}
                
                outputs = result.get("outputs", {})
                
                emit_progress(workflow_name, node_id, "completed", {
                    "description": node["progress"]["completed"],
                    **outputs
                })
                
                return outputs
                
            except Exception as e:
                logger.error(f"❌ 节点执行异常: {e}", exc_info=True)
                emit_progress(workflow_name, node_id, "failed", {
                    "description": node["progress"]["failed"],
                    "error": str(e)
                })
                return {"errors": [f"{node['name']}异常: {str(e)}"]}
        
        return script_node
    
    def _create_tool_node(self, node_id: str, node: dict, workflow_name: str) -> Callable:
        """创建工具节点"""
        tool_config = node["tool"]
        tool_name = tool_config["name"]
        
        if tool_name not in self.tools:
            raise ValueError(f"工具不存在: {tool_name}")
        
        tool = self.tools[tool_name]
        
        def tool_node(state: dict) -> dict:
            emit_progress(workflow_name, node_id, "started", {
                "description": node["progress"]["started"]
            })
            
            try:
                tool_params = {}
                for key, value in tool_config["params"].items():
                    if isinstance(value, str) and value.startswith("{") and value.endswith("}"):
                        param_name = value[1:-1]
                        tool_params[key] = state.get(param_name)
                    else:
                        tool_params[key] = value
                
                result = tool.invoke(tool_params)
                
                if not result.get("success"):
                    error_msg = result.get("error", "未知错误")
                    emit_progress(workflow_name, node_id, "failed", {
                        "description": node["progress"]["failed"],
                        "error": error_msg
                    })
                    return {"errors": [f"{node['name']}失败: {error_msg}"]}
                
                outputs = {}
                if node.get("outputs"):
                    output_key = node["outputs"][0]
                    outputs[output_key] = result.get("data")
                
                emit_progress(workflow_name, node_id, "completed", {
                    "description": node["progress"]["completed"]
                })
                
                return outputs
                
            except Exception as e:
                logger.error(f"❌ 工具节点执行异常: {e}", exc_info=True)
                emit_progress(workflow_name, node_id, "failed", {
                    "description": node["progress"]["failed"],
                    "error": str(e)
                })
                return {"errors": [f"{node['name']}异常: {str(e)}"]}
        
        return tool_node
    
    def _create_human_node(self, node_id: str, node: dict, workflow_name: str) -> Callable:
        """创建人工审批节点"""
        def human_node(state: dict) -> dict:
            emit_progress(workflow_name, node_id, "started", {
                "description": node["progress"]["started"],
                "requires_human_input": True
            })
            
            return {
                "approved": True,
                "review_comment": "自动通过(演示模式)"
            }
        
        return human_node
    
    def _create_condition_function(self, condition: dict) -> Callable:
        """创建条件函数"""
        field = condition["field"]
        operator = condition["operator"]
        value = condition["value"]
        
        def condition_func(state: dict) -> bool:
            state_value = state.get(field)
            
            if operator == "==":
                return state_value == value
            elif operator == "!=":
                return state_value != value
            elif operator == ">":
                return state_value > value
            elif operator == "<":
                return state_value < value
            elif operator == ">=":
                return state_value >= value
            elif operator == "<=":
                return state_value <= value
            elif operator == "in":
                return state_value in value
            elif operator == "not in":
                return state_value not in value
            else:
                raise ValueError(f"不支持的操作符: {operator}")
        
        return condition_func
    
    def _run_script(self, script_path: Path, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """运行Python脚本"""
        if not script_path.exists():
            return {
                "success": False,
                "error": f"脚本文件不存在: {script_path}"
            }
        
        inputs_json = json.dumps(inputs, ensure_ascii=False)
        
        result = subprocess.run(
            [sys.executable, str(script_path)],
            input=inputs_json,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            return {
                "success": False,
                "error": result.stderr or "脚本执行失败"
            }
        
        try:
            output = json.loads(result.stdout)
            return output
        except json.JSONDecodeError:
            return {
                "success": False,
                "error": f"脚本输出不是有效的JSON: {result.stdout}"
            }
    
    def get_metadata(self) -> dict:
        """获取工作流元数据"""
        return {
            "name": self.config["name"],
            "version": self.config["version"],
            "description": self.config["description"],
            "parameters": self.config.get("parameters", {}),
            "outputs": self.config.get("outputs", {}),
            "metadata": self.config.get("metadata", {})
        }
