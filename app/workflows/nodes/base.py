from typing import Dict, Any, Callable, Optional
from abc import ABC, abstractmethod


_progress_callback: Optional[Callable[[dict], None]] = None


def set_workflow_progress_callback(callback: Callable[[dict], None]):
    global _progress_callback
    _progress_callback = callback


def clear_workflow_progress_callback():
    global _progress_callback
    _progress_callback = None


def _emit_progress(progress_data: dict):
    global _progress_callback
    if _progress_callback:
        _progress_callback(progress_data)


class BaseNode(ABC):
    def __init__(self, node_id: str, node_config: Dict[str, Any]):
        self.node_id = node_id
        self.node_config = node_config
    
    @abstractmethod
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        pass
