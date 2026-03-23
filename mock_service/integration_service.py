#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mock集成服务
"""

class MockIntegrationService:
    """Mock集成服务"""
    
    def __init__(self):
        self.tasks = {}
        self.task_id_counter = 1
    
    def create_task(self, task_data):
        """创建任务"""
        task_id = f"task_{self.task_id_counter}"
        self.task_id_counter += 1
        
        self.tasks[task_id] = {
            "id": task_id,
            "status": "pending",
            "type": task_data.get("task_type", "full"),
            "source_config": task_data.get("source_config", {}),
            "target_config": task_data.get("target_config", {}),
            "created_at": "2026-03-16T00:00:00"
        }
        
        return {"task_id": task_id, "status": "created"}
    
    def get_task_status(self, task_id):
        """获取任务状态"""
        if task_id in self.tasks:
            # 模拟任务执行
            if self.tasks[task_id]["status"] == "pending":
                self.tasks[task_id]["status"] = "running"
            elif self.tasks[task_id]["status"] == "running":
                self.tasks[task_id]["status"] = "success"
            
            return self.tasks[task_id]
        return {"error": "Task not found"}
    
    def list_tasks(self):
        """列出所有任务"""
        return {"tasks": list(self.tasks.values())}
