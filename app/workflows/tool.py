import json
import uuid
from typing import Dict, Any
from langchain.tools import tool
from .loader import load_workflow_definition
from .engine import compile_workflow_to_langgraph
from .error_handler import format_error_for_agent
from .nodes.base import set_workflow_progress_callback, _emit_progress


def get_node_name(workflow_json: Dict[str, Any], node_id: str) -> str:
    for node in workflow_json.get("nodes", []):
        if node["id"] == node_id:
            return node.get("name", node_id)
    return node_id


@tool
async def execute_workflow(workflow_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    执行工作流 - 编译JSON并流式执行
    
    Args:
        workflow_name: 工作流名称（对应workflows/definitions/{workflow_name}.json）
        params: 工作流输入参数
        
    Returns:
        Dict包含:
        - success: bool
        - result: 工作流最终结果（给智能体看）
        - error: 错误信息（如果失败）
        - execution_trace: 执行轨迹
    """
    try:
        workflow_json = load_workflow_definition(workflow_name)
        
        graph = compile_workflow_to_langgraph(workflow_json)
        
        state = {
            "input": params,
            "data": {},
            "result": None,
            "it": {
                "workflow_name": workflow_name,
                "trace_id": str(uuid.uuid4()),
                "user_id": params.get("_user_id"),
                "conversation_id": params.get("_conversation_id")
            },
            "_execution_trace": [],
            "_current_node": None
        }
        
        async for event in graph.astream(state, stream_mode="updates"):
            for node_id, node_update in event.items():
                if node_id.startswith("__"):
                    continue
                
                node_data = node_update.get("data", {}).get(node_id)
                
                if isinstance(node_data, dict) and node_data.get("status") == "error":
                    error_info = node_data.get("error")
                    
                    _emit_progress({
                        "type": "node_error",
                        "workflow_name": workflow_name,
                        "node_id": node_id,
                        "node_name": get_node_name(workflow_json, node_id),
                        "error": error_info
                    })
                    
                    return {
                        "success": False,
                        "result": None,
                        "error": format_error_for_agent(
                            workflow_name=workflow_name,
                            node_id=node_id,
                            node_name=get_node_name(workflow_json, node_id),
                            error_info=error_info,
                            execution_trace=state["_execution_trace"]
                        ),
                        "execution_trace": state["_execution_trace"]
                    }
                
                _emit_progress({
                    "type": "node_completed",
                    "workflow_name": workflow_name,
                    "node_id": node_id,
                    "node_name": get_node_name(workflow_json, node_id),
                    "status": "completed",
                    "data": node_data
                })
        
        result_text = state.get("result") or f"工作流 {workflow_name} 执行成功"
        
        return {
            "success": True,
            "result": result_text,
            "error": None,
            "execution_trace": state["_execution_trace"]
        }
        
    except Exception as e:
        return {
            "success": False,
            "result": None,
            "error": f"工作流执行失败: {str(e)}",
            "execution_trace": []
        }
