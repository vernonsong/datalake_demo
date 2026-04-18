import time
import traceback
import linecache
from typing import Dict, Any, Callable
from langgraph.graph import StateGraph, END
from .state import WorkflowState
from .nodes import PythonExecutorNode, LLMNode, HTTPRequestNode, MapNode


NODE_TYPE_MAP = {
    "python_executor": PythonExecutorNode,
    "llm": LLMNode,
    "http_request": HTTPRequestNode,
    "map": MapNode,
}


def compile_workflow_to_langgraph(workflow_json: Dict[str, Any]) -> StateGraph:
    graph = StateGraph(WorkflowState)
    
    nodes_dict = {node["id"]: node for node in workflow_json["nodes"]}
    
    for node in workflow_json["nodes"]:
        node_id = node["id"]
        node_type = node["type"]
        
        if node_type not in NODE_TYPE_MAP:
            raise ValueError(f"不支持的节点类型: {node_type}")
        
        node_class = NODE_TYPE_MAP[node_type]
        node_instance = node_class(node_id, node)
        
        node_func = create_node_wrapper(node_id, node, node_instance)
        graph.add_node(node_id, node_func)
    
    for edge in workflow_json["edges"]:
        from_node = edge["from"]
        to_node = edge["to"]
        graph.add_edge(from_node, to_node)
    
    if workflow_json["nodes"]:
        first_node = workflow_json["nodes"][0]["id"]
        graph.set_entry_point(first_node)
    
    last_nodes = find_last_nodes(workflow_json)
    for last_node in last_nodes:
        graph.add_edge(last_node, END)
    
    return graph.compile()


def create_node_wrapper(node_id: str, node_config: Dict[str, Any], node_instance) -> Callable:
    async def node_func(state: Dict[str, Any]) -> Dict[str, Any]:
        start_time = time.time()
        
        try:
            result = await node_instance.execute(state)
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            if result.get("status") == "error":
                state["_execution_trace"].append({
                    "node_id": node_id,
                    "node_name": node_config.get("name", node_id),
                    "node_type": node_config["type"],
                    "status": "error",
                    "start_time": start_time,
                    "duration_ms": duration_ms,
                    "error": result.get("error")
                })
                
                return {
                    "_current_node": node_id,
                    "data": {node_id: result},
                    "_execution_trace": state["_execution_trace"]
                }
            
            state["_execution_trace"].append({
                "node_id": node_id,
                "node_name": node_config.get("name", node_id),
                "node_type": node_config["type"],
                "status": "success",
                "start_time": start_time,
                "duration_ms": duration_ms
            })
            
            return {
                "_current_node": node_id,
                "data": {node_id: result.get("output")},
                "_execution_trace": state["_execution_trace"]
            }
            
        except Exception as e:
            tb = traceback.extract_tb(e.__traceback__)
            frame = tb[-1] if tb else None
            
            error_info = {
                "type": type(e).__name__,
                "message": str(e),
                "traceback": traceback.format_exc()
            }
            
            if frame:
                error_info.update({
                    "file": frame.filename,
                    "line": frame.lineno,
                    "code_snippet": linecache.getline(frame.filename, frame.lineno).strip()
                })
            
            duration_ms = int((time.time() - start_time) * 1000)
            state["_execution_trace"].append({
                "node_id": node_id,
                "node_name": node_config.get("name", node_id),
                "node_type": node_config["type"],
                "status": "error",
                "start_time": start_time,
                "duration_ms": duration_ms,
                "error": error_info
            })
            
            return {
                "_current_node": node_id,
                "data": {node_id: {"status": "error", "error": error_info}},
                "_execution_trace": state["_execution_trace"]
            }
    
    return node_func


def find_last_nodes(workflow_json: Dict[str, Any]) -> list:
    all_nodes = {node["id"] for node in workflow_json["nodes"]}
    nodes_with_outgoing = {edge["from"] for edge in workflow_json["edges"]}
    
    last_nodes = all_nodes - nodes_with_outgoing
    
    return list(last_nodes) if last_nodes else [workflow_json["nodes"][-1]["id"]]


async def execute_workflow_stream(workflow_json: Dict[str, Any], params: Dict[str, Any]):
    graph = compile_workflow_to_langgraph(workflow_json)
    
    state = {
        "input": params,
        "data": {},
        "result": None,
        "it": params.get("_it", {}),
        "_execution_trace": [],
        "_current_node": None
    }
    
    async for event in graph.astream(state, stream_mode="updates"):
        yield event
