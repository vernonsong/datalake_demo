#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mock调度服务
"""

class MockScheduleService:
    """Mock调度服务"""
    
    def __init__(self):
        self.schedules = {}
        self.schedule_id_counter = 1
    
    def create_schedule(self, schedule_data):
        """创建调度任务"""
        schedule_id = f"schedule_{self.schedule_id_counter}"
        self.schedule_id_counter += 1
        
        self.schedules[schedule_id] = {
            "id": schedule_id,
            "name": schedule_data.get("schedule_name", "unnamed"),
            "task_id": schedule_data.get("task_id"),
            "cron_expression": schedule_data.get("cron_expression", "0 0 * * *"),
            "status": "active",
            "created_at": "2026-03-16T00:00:00"
        }
        
        return {"schedule_id": schedule_id, "status": "created"}
    
    def get_schedule(self, schedule_id):
        """获取调度任务"""
        if schedule_id in self.schedules:
            return self.schedules[schedule_id]
        return {"error": "Schedule not found"}
    
    def list_schedules(self):
        """列出所有调度任务"""
        return {"schedules": list(self.schedules.values())}
    
    def update_schedule(self, schedule_id, updates):
        """更新调度任务"""
        if schedule_id in self.schedules:
            self.schedules[schedule_id].update(updates)
            return {"status": "updated"}
        return {"error": "Schedule not found"}
