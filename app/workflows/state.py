from typing import TypedDict, Any, Dict, Optional, List
from typing_extensions import Annotated
from operator import add


def aggregate_map_results(existing: List[Dict[str, Any]], new: Dict[str, Any]) -> List[Dict[str, Any]]:
    """聚合Map节点的结果"""
    if "_map_result" in new:
        return existing + [new["_map_result"]]
    return existing


class WorkflowState(TypedDict):
    input: Dict[str, Any]
    data: Dict[str, Any]
    result: Optional[str]
    it: Dict[str, Any]
    _execution_trace: List[Dict[str, Any]]
    _current_node: Optional[str]
    _map_results: Annotated[List[Dict[str, Any]], aggregate_map_results]
