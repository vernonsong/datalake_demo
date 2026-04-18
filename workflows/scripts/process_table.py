from typing import Dict, Any
import time


def codehandler(state: Dict[str, Any]) -> Dict[str, Any]:
    table = state["input"].get("table")
    
    if not table:
        raise ValueError("缺少table参数")
    
    table_name = table.get("table_name")
    columns = table.get("columns", 0)
    
    time.sleep(0.1)
    
    return {
        "table_name": table_name,
        "columns": columns,
        "processed": True,
        "rows_processed": columns * 100
    }
