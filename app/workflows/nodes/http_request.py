import re
import traceback
import httpx
from typing import Dict, Any
from .base import BaseNode


class HTTPRequestNode(BaseNode):
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        config = self.node_config.get("config", {})
        method = config.get("method", "GET")
        url = config.get("url")
        
        if not url:
            raise ValueError(f"节点{self.node_id}缺少url配置")
        
        try:
            url = self._resolve_template(url, state)
            headers = self._resolve_dict(config.get("headers", {}), state)
            body = self._resolve_dict(config.get("body", {}), state)
            timeout = config.get("timeout", 30)
            
            async with httpx.AsyncClient() as client:
                if method.upper() == "GET":
                    response = await client.get(url, headers=headers, timeout=timeout)
                elif method.upper() == "POST":
                    response = await client.post(url, headers=headers, json=body, timeout=timeout)
                elif method.upper() == "PUT":
                    response = await client.put(url, headers=headers, json=body, timeout=timeout)
                elif method.upper() == "DELETE":
                    response = await client.delete(url, headers=headers, timeout=timeout)
                else:
                    raise ValueError(f"不支持的HTTP方法: {method}")
                
                response.raise_for_status()
                
                return {
                    "status": "success",
                    "output": {
                        "status_code": response.status_code,
                        "body": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
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
    
    def _resolve_dict(self, template_dict: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        result = {}
        for key, value in template_dict.items():
            if isinstance(value, str):
                result[key] = self._resolve_template(value, state)
            elif isinstance(value, dict):
                result[key] = self._resolve_dict(value, state)
            else:
                result[key] = value
        return result
