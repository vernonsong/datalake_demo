import re
import traceback
from typing import Dict, Any, List
from langgraph.types import Send
from .base import BaseNode, _emit_progress
from ..loader import load_workflow_definition
from ..error_handler import MapNodeExecutionError


class MapNode(BaseNode):
    """
    Map节点 - 使用LangGraph的Send API实现并行处理
    
    工作流程:
    1. map_dispatch: 分发任务，返回Send对象列表
    2. map_process: 并行处理每个项目
    3. map_reduce: 聚合所有结果
    """
    
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any] | List[Send]:
        config = self.node_config.get("config", {})
        input_expr = config.get("input")
        sub_workflow_name = config.get("sub_workflow")
        item_name = config.get("item_name", "item")
        
        if not input_expr:
            raise ValueError(f"节点{self.node_id}缺少input配置")
        if not sub_workflow_name:
            raise ValueError(f"节点{self.node_id}缺少sub_workflow配置")
        
        try:
            input_array = self._resolve_expression(input_expr, state)
            
            if not isinstance(input_array, list):
                raise ValueError(f"Map节点输入必须是数组，实际类型: {type(input_array)}")
            
            _emit_progress({
                "type": "map_dispatch",
                "node_id": self.node_id,
                "node_name": self.node_config.get("name", self.node_id),
                "sub_workflow": sub_workflow_name,
                "total_items": len(input_array),
                "status": "dispatching"
            })
            
            sends = []
            for index, item in enumerate(input_array):
                map_state = {
                    **state,
                    "_map_item": item,
                    "_map_index": index,
                    "_map_total": len(input_array),
                    "_map_parent_node": self.node_id,
                    "_map_sub_workflow": sub_workflow_name,
                    "_map_item_name": item_name
                }
                
                sends.append(Send(f"{self.node_id}_process", map_state))
            
            return sends
            
        except Exception as e:
            return {
                "status": "error",
                "error": {
                    "type": type(e).__name__,
                    "message": str(e),
                    "traceback": traceback.format_exc()
                }
            }
    
    def _resolve_expression(self, expr: str, state: Dict[str, Any]) -> Any:
        pattern = r'\$\{([^}]+)\}'
        match = re.search(pattern, expr)
        if match:
            var_path = match.group(1)
            parts = var_path.split(".")
            
            value = state
            for part in parts:
                if value is None:
                    return None
                if isinstance(value, dict):
                    value = value.get(part)
                elif isinstance(value, list):
                    try:
                        value = value[int(part)]
                    except (ValueError, IndexError):
                        return None
                else:
                    return None
            
            return value
        return expr


class MapProcessNode(BaseNode):
    """处理单个Map项目的节点"""
    
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        item = state.get("_map_item")
        index = state.get("_map_index")
        total = state.get("_map_total")
        parent_node = state.get("_map_parent_node")
        sub_workflow_name = state.get("_map_sub_workflow")
        item_name = state.get("_map_item_name", "item")
        
        try:
            _emit_progress({
                "type": "map_item_start",
                "parent_node": parent_node,
                "sub_workflow": sub_workflow_name,
                "item_index": index,
                "total_items": total,
                "item_data": item
            })
            
            sub_workflow_json = load_workflow_definition(sub_workflow_name)
            
            from ..engine import compile_workflow_to_langgraph
            sub_graph = compile_workflow_to_langgraph(sub_workflow_json)
            
            sub_state = {
                "input": {
                    item_name: item,
                    "index": index
                },
                "data": {},
                "result": None,
                "it": state.get("it", {}),
                "_execution_trace": [],
                "_current_node": None,
                "_parent_node": parent_node,
                "_map_context": {
                    "index": index,
                    "total": total
                }
            }
            
            async for event in sub_graph.astream(sub_state, stream_mode="updates"):
                for node_id, node_output in event.items():
                    if node_id.startswith("__"):
                        continue
                    
                    if node_output.get("status") == "error":
                        error_info = node_output.get("error")
                        
                        _emit_progress({
                            "type": "map_item_error",
                            "parent_node": parent_node,
                            "sub_workflow": sub_workflow_name,
                            "item_index": index,
                            "node_id": node_id,
                            "node_name": self._get_node_name(sub_workflow_json, node_id),
                            "error": error_info
                        })
                        
                        raise MapNodeExecutionError(
                            parent_node=parent_node,
                            sub_workflow=sub_workflow_name,
                            item_index=index,
                            node_id=node_id,
                            node_name=self._get_node_name(sub_workflow_json, node_id),
                            error_info=error_info
                        )
                    
                    _emit_progress({
                        "type": "map_item_progress",
                        "parent_node": parent_node,
                        "sub_workflow": sub_workflow_name,
                        "item_index": index,
                        "node_id": node_id,
                        "node_name": self._get_node_name(sub_workflow_json, node_id),
                        "status": "completed"
                    })
            
            _emit_progress({
                "type": "map_item_completed",
                "parent_node": parent_node,
                "sub_workflow": sub_workflow_name,
                "item_index": index,
                "total_items": total
            })
            
            return {
                "_map_result": {
                    "index": index,
                    "item": item,
                    "result": sub_state["result"],
                    "success": True
                }
            }
            
        except Exception as e:
            if isinstance(e, MapNodeExecutionError):
                raise
            
            return {
                "status": "error",
                "error": {
                    "type": type(e).__name__,
                    "message": str(e),
                    "traceback": traceback.format_exc()
                }
            }
    
    def _get_node_name(self, workflow_json: Dict[str, Any], node_id: str) -> str:
        for node in workflow_json.get("nodes", []):
            if node["id"] == node_id:
                return node.get("name", node_id)
        return node_id


class MapReduceNode(BaseNode):
    """聚合Map结果的节点"""
    
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        map_results = state.get("_map_results", [])
        
        map_results.sort(key=lambda x: x.get("index", 0))
        
        _emit_progress({
            "type": "map_reduce",
            "node_id": self.node_id,
            "node_name": self.node_config.get("name", self.node_id),
            "total_results": len(map_results),
            "status": "completed"
        })
        
        return {
            "status": "success",
            "output": map_results
        }
