#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试中断判断逻辑
"""

import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.core.dependencies import _should_interrupt_platform_service, _resolve_doc_path


class TestInterruptLogic(unittest.TestCase):
    """测试中断判断逻辑"""
    
    def test_resolve_doc_path_relative(self):
        """测试解析相对路径"""
        doc_path = "skills/platform-skill/metadata-service/get-table-schema.md"
        resolved = _resolve_doc_path(doc_path)
        
        self.assertTrue(resolved.exists())
        self.assertTrue(resolved.is_file())
    
    def test_should_interrupt_create_task(self):
        """测试创建任务接口（需要中断）"""
        tool_call = {
            "args": {
                "doc_path": "skills/platform-skill/integration-service/create-task.md"
            }
        }
        
        result = _should_interrupt_platform_service(tool_call)
        
        self.assertTrue(result, "创建任务接口应该需要用户确认")
    
    def test_should_not_interrupt_get_schema(self):
        """测试查询表结构接口（不需要中断）"""
        tool_call = {
            "args": {
                "doc_path": "skills/platform-skill/metadata-service/get-table-schema.md"
            }
        }
        
        result = _should_interrupt_platform_service(tool_call)
        
        self.assertFalse(result, "查询接口不应该需要用户确认")
    
    def test_should_interrupt_create_schedule(self):
        """测试创建调度接口（需要中断）"""
        tool_call = {
            "args": {
                "doc_path": "skills/platform-skill/schedule-service/create-schedule.md"
            }
        }
        
        result = _should_interrupt_platform_service(tool_call)
        
        self.assertTrue(result, "创建调度接口应该需要用户确认")
    
    def test_should_not_interrupt_list_tasks(self):
        """测试查询任务列表接口（不需要中断）"""
        tool_call = {
            "args": {
                "doc_path": "skills/platform-skill/integration-service/list-tasks.md"
            }
        }
        
        result = _should_interrupt_platform_service(tool_call)
        
        self.assertFalse(result, "查询接口不应该需要用户确认")
    
    def test_missing_doc_path(self):
        """测试缺少doc_path参数"""
        tool_call = {
            "args": {}
        }
        
        result = _should_interrupt_platform_service(tool_call)
        
        self.assertFalse(result, "缺少doc_path时默认不中断")
    
    def test_nonexistent_doc(self):
        """测试文档不存在的情况"""
        tool_call = {
            "args": {
                "doc_path": "skills/platform-skill/nonexistent.md"
            }
        }
        
        result = _should_interrupt_platform_service(tool_call)
        
        self.assertTrue(result, "文档不存在时为安全起见应该中断")


if __name__ == "__main__":
    unittest.main()
