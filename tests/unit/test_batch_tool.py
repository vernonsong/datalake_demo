#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量处理工具测试
"""

import unittest
import json
from unittest.mock import Mock, patch
from app.agents.tools.batch_tool import batch_process


class TestBatchTool(unittest.TestCase):
    """测试批量处理工具"""
    
    def test_batch_process_empty_list(self):
        """测试空列表"""
        result = batch_process.invoke({
            "items": "[]",
            "instruction_template": "处理{单号}",
            "batch_size": 5
        })
        
        self.assertTrue(result["success"])
        self.assertEqual(result["total"], 0)
        self.assertEqual(result["processed"], 0)
    
    def test_batch_process_invalid_json(self):
        """测试无效JSON"""
        result = batch_process.invoke({
            "items": "not a json",
            "instruction_template": "处理{单号}",
            "batch_size": 5
        })
        
        self.assertFalse(result["success"])
        self.assertIn("JSON", result["error"])
    
    def test_batch_process_not_array(self):
        """测试非数组JSON"""
        result = batch_process.invoke({
            "items": '{"key": "value"}',
            "instruction_template": "处理{单号}",
            "batch_size": 5
        })
        
        self.assertFalse(result["success"])
        self.assertIn("数组", result["error"])
    
    @patch('app.core.dependencies.get_deep_agent')
    def test_batch_process_success(self, mock_get_agent):
        """测试成功的批量处理"""
        mock_agent = Mock()
        mock_agent.invoke.return_value = {
            "messages": [
                Mock(content="处理完成")
            ]
        }
        mock_get_agent.return_value = mock_agent
        
        items = [
            {"单号": "ORDER001", "源表": "table1"},
            {"单号": "ORDER002", "源表": "table2"}
        ]
        
        result = batch_process.invoke({
            "items": json.dumps(items),
            "instruction_template": "处理单号{单号}，源表{源表}",
            "batch_size": 5
        })
        
        self.assertTrue(result["success"])
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["total"], 2)
        self.assertEqual(result["processed"], 2)
        self.assertEqual(result["success_count"], 2)
        self.assertEqual(result["fail_count"], 0)
        self.assertEqual(len(result["results"]), 2)
        
        self.assertEqual(mock_agent.invoke.call_count, 2)
    
    @patch('app.core.dependencies.get_deep_agent')
    def test_batch_process_partial(self, mock_get_agent):
        """测试分批处理"""
        mock_agent = Mock()
        mock_agent.invoke.return_value = {
            "messages": [
                Mock(content="处理完成")
            ]
        }
        mock_get_agent.return_value = mock_agent
        
        items = [
            {"单号": f"ORDER{i:03d}", "源表": f"table{i}"}
            for i in range(1, 8)
        ]
        
        result = batch_process.invoke({
            "items": json.dumps(items),
            "instruction_template": "处理单号{单号}",
            "batch_size": 5
        })
        
        self.assertTrue(result["success"])
        self.assertEqual(result["status"], "partial")
        self.assertEqual(result["total"], 7)
        self.assertEqual(result["processed"], 5)
        self.assertEqual(result["remaining"], 2)
        
        self.assertEqual(mock_agent.invoke.call_count, 5)
    
    @patch('app.core.dependencies.get_deep_agent')
    def test_batch_process_with_failure(self, mock_get_agent):
        """测试包含失败的批量处理"""
        mock_agent = Mock()
        
        def side_effect(*args, **kwargs):
            content = args[0]["messages"][0]["content"]
            if "ORDER002" in content:
                raise Exception("处理失败")
            return {
                "messages": [Mock(content="处理完成")]
            }
        
        mock_agent.invoke.side_effect = side_effect
        mock_get_agent.return_value = mock_agent
        
        items = [
            {"单号": "ORDER001"},
            {"单号": "ORDER002"},
            {"单号": "ORDER003"}
        ]
        
        result = batch_process.invoke({
            "items": json.dumps(items),
            "instruction_template": "处理单号{单号}",
            "batch_size": 5
        })
        
        self.assertTrue(result["success"])
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["total"], 3)
        self.assertEqual(result["processed"], 2)
        self.assertEqual(result["success_count"], 2)
        self.assertEqual(result["fail_count"], 1)
        
        failed_result = [r for r in result["results"] if r["status"] == "failed"][0]
        self.assertEqual(failed_result["item"]["单号"], "ORDER002")


if __name__ == "__main__":
    unittest.main()
