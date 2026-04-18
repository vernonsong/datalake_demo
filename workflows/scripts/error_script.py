from typing import Dict, Any


def codehandler(state: Dict[str, Any]) -> Dict[str, Any]:
    value = state["input"].get("value")
    
    result = int(value)
    
    return {
        "result": result
    }
