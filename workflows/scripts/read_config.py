from typing import Dict, Any


def codehandler(state: Dict[str, Any]) -> Dict[str, Any]:
    file_name = state["input"].get("file_name", "config.json")
    
    tables = [
        {"table_name": "users", "columns": 10},
        {"table_name": "orders", "columns": 15},
        {"table_name": "products", "columns": 8}
    ]
    
    return {
        "file_name": file_name,
        "tables": tables,
        "count": len(tables)
    }
