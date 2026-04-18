from typing import Dict, Any, Optional, List


class WorkflowExecutionError(Exception):
    def to_agent_message(self) -> str:
        raise NotImplementedError


class NodeExecutionError(WorkflowExecutionError):
    def __init__(
        self,
        workflow_name: str,
        node_id: str,
        node_name: str,
        node_type: str,
        original_error: Exception,
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
        code_snippet: Optional[str] = None,
        execution_trace: Optional[List[Dict]] = None
    ):
        self.workflow_name = workflow_name
        self.node_id = node_id
        self.node_name = node_name
        self.node_type = node_type
        self.original_error = original_error
        self.file_path = file_path
        self.line_number = line_number
        self.code_snippet = code_snippet
        self.execution_trace = execution_trace or []
        super().__init__(self.to_agent_message())
    
    def to_agent_message(self) -> str:
        msg = f"""工作流执行中断:

工作流: {self.workflow_name}
中断节点: {self.node_name} (ID: {self.node_id})
节点类型: {self.node_type}

错误原因:
{type(self.original_error).__name__}: {str(self.original_error)}
"""
        
        if self.file_path and self.line_number:
            msg += f"""
错误位置:
文件: {self.file_path}
行号: {self.line_number}
代码: {self.code_snippet}
"""
        
        if self.execution_trace:
            msg += "\n执行轨迹:\n"
            for i, trace in enumerate(self.execution_trace, 1):
                status_icon = "✅" if trace["status"] == "success" else "❌"
                msg += f"{i}. {status_icon} {trace['node_name']} ({trace['duration_ms']}ms)\n"
        
        return msg


class MapNodeExecutionError(WorkflowExecutionError):
    def __init__(
        self,
        parent_node: str,
        sub_workflow: str,
        item_index: int,
        node_id: str,
        node_name: str,
        error_info: Dict[str, Any]
    ):
        self.parent_node = parent_node
        self.sub_workflow = sub_workflow
        self.item_index = item_index
        self.node_id = node_id
        self.node_name = node_name
        self.error_info = error_info
        super().__init__(self.to_agent_message())
    
    def to_agent_message(self) -> str:
        return f"""工作流执行中断:

Map节点: {self.parent_node}
子工作流: {self.sub_workflow}
处理项索引: {self.item_index}
中断节点: {self.node_name} (ID: {self.node_id})

错误原因:
{self.error_info.get('type', 'Unknown')}: {self.error_info.get('message', 'No message')}

错误位置:
文件: {self.error_info.get('file', 'Unknown')}
行号: {self.error_info.get('line', 'Unknown')}
代码: {self.error_info.get('code_snippet', 'N/A')}
"""


def format_error_for_agent(
    workflow_name: str,
    node_id: str,
    node_name: str,
    error_info: Dict[str, Any],
    execution_trace: List[Dict[str, Any]]
) -> str:
    msg = f"""工作流执行中断:

工作流: {workflow_name}
中断节点: {node_name} (ID: {node_id})

错误原因:
{error_info.get('type', 'Unknown')}: {error_info.get('message', 'No message')}
"""
    
    if error_info.get('file') and error_info.get('line'):
        msg += f"""
错误位置:
文件: {error_info['file']}
行号: {error_info['line']}
代码: {error_info.get('code_snippet', 'N/A')}
"""
    
    if execution_trace:
        msg += "\n执行轨迹:\n"
        for i, trace in enumerate(execution_trace, 1):
            status_icon = "✅" if trace["status"] == "success" else "❌"
            msg += f"{i}. {status_icon} {trace['node_name']} ({trace.get('duration_ms', 0)}ms)\n"
    
    return msg
