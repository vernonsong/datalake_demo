import importlib.util
import sys
import traceback
import linecache
from pathlib import Path
from typing import Dict, Any
from .base import BaseNode


class PythonExecutorNode(BaseNode):
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        config = self.node_config.get("config", {})
        script_path = config.get("script_path")
        
        if not script_path:
            raise ValueError(f"节点{self.node_id}缺少script_path配置")
        
        path = Path(script_path).resolve()
        
        if not path.exists():
            raise FileNotFoundError(f"脚本文件不存在: {script_path}")
        
        module = self._load_script_module(path)
        
        if not hasattr(module, "codehandler"):
            raise AttributeError(f"脚本{script_path}缺少codehandler函数")
        
        codehandler = getattr(module, "codehandler")
        
        try:
            result = codehandler(state)
            
            return {
                "status": "success",
                "output": result
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
            
            return {
                "status": "error",
                "error": error_info
            }
    
    def _load_script_module(self, script_path: Path):
        spec = importlib.util.spec_from_file_location(
            f"workflow_script_{script_path.stem}",
            script_path
        )
        module = importlib.util.module_from_spec(spec)
        
        sys.modules[spec.name] = module
        
        spec.loader.exec_module(module)
        return module
