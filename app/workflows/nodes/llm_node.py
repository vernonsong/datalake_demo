import re
import traceback
from typing import Dict, Any
from .base import BaseNode


class LLMNode(BaseNode):
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        config = self.node_config.get("config", {})
        prompt_template = config.get("prompt_template")
        
        if not prompt_template:
            raise ValueError(f"节点{self.node_id}缺少prompt_template配置")
        
        try:
            prompt = self._resolve_template(prompt_template, state)
            
            response = f"LLM响应: {prompt[:50]}..."
            
            return {
                "status": "success",
                "output": {
                    "prompt": prompt,
                    "response": response
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "error": {
                    "type": type(e).__name__,
                    "message": str(e),
                    "traceback": traceback.format_exc()
                }
            }
    
    def _resolve_template(self, template: str, state: Dict[str, Any]) -> str:
        def replace_var(match):
            var_path = match.group(1)
            parts = var_path.split(".")
            
            value = state
            for part in parts:
                if isinstance(value, dict):
                    value = value.get(part)
                else:
                    return match.group(0)
            
            return str(value) if value is not None else match.group(0)
        
        return re.sub(r'\$\{([^}]+)\}', replace_var, template)
