#!/usr/bin/env python3
"""快速测试中断逻辑是否生效"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from app.core.dependencies import _should_interrupt_platform_service

# 测试 SQL 服务的 request-sql.md
tool_call = {
    "name": "platform_service",
    "args": {
        "doc_path": "skills/platform-skill/sql-service/request-sql.md",
        "platform": "sql",
        "method": "POST",
        "endpoint": "/api/sql/request"
    }
}

result = _should_interrupt_platform_service(tool_call)
print(f"SQL request-sql.md - Should interrupt: {result}")
print(f"Expected: True")
print(f"Result: {'✅ PASS' if result == True else '❌ FAIL'}")

# 测试集成服务的 create-task.md
tool_call2 = {
    "name": "platform_service",
    "args": {
        "doc_path": "skills/platform-skill/integration-service/create-task.md"
    }
}

result2 = _should_interrupt_platform_service(tool_call2)
print(f"\nIntegration create-task.md - Should interrupt: {result2}")
print(f"Expected: True")
print(f"Result: {'✅ PASS' if result2 == True else '❌ FAIL'}")

# 测试元数据服务的 get-table-schema.md
tool_call3 = {
    "name": "platform_service",
    "args": {
        "doc_path": "skills/platform-skill/metadata-service/get-table-schema.md"
    }
}

result3 = _should_interrupt_platform_service(tool_call3)
print(f"\nMetadata get-table-schema.md - Should interrupt: {result3}")
print(f"Expected: False")
print(f"Result: {'✅ PASS' if result3 == False else '❌ FAIL'}")
