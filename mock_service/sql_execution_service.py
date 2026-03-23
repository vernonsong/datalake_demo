#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mock SQL执行服务
"""

class MockSqlExecutionService:
    """Mock SQL执行服务"""
    
    def __init__(self):
        self.executions = {}
        self.execution_id_counter = 1
    
    def execute_sql(self, sql_data):
        """执行SQL"""
        execution_id = f"exec_{self.execution_id_counter}"
        self.execution_id_counter += 1
        
        # 模拟SQL执行结果
        result = {
            "id": execution_id,
            "status": "success",
            "sql": sql_data.get("sql"),
            "database": sql_data.get("database"),
            "rows_affected": 100,
            "execution_time": 0.5,
            "result": [
                {"id": 1, "name": "test", "value": 100},
                {"id": 2, "name": "demo", "value": 200}
            ]
        }
        
        self.executions[execution_id] = result
        return result
    
    def get_execution_status(self, execution_id):
        """获取执行状态"""
        if execution_id in self.executions:
            return self.executions[execution_id]
        return {"error": "Execution not found"}
    
    def list_executions(self):
        """列出所有执行记录"""
        return {"executions": list(self.executions.values())}
