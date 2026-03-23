#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务完成验证器
通过模拟对话验证智能体功能
"""

import os
import sys
import time
import requests
from pathlib import Path
import json


class TaskCompletionValidator:
    """任务完成验证器"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.errors = []
        self.warnings = []
        self.api_base = "http://localhost:8000"

    def validate(self) -> bool:
        """执行验证"""
        self.errors = []
        self.warnings = []

        self._validate_tests()
        self._validate_imports()
        self._validate_config()
        self._validate_structure()
        self._validate_chat_api()

        if self.errors:
            print("\n❌ 验证失败:")
            for error in self.errors:
                print(f"  - {error}")
            return False

        if self.warnings:
            print("\n⚠️ 警告:")
            for warning in self.warnings:
                print(f"  - {warning}")

        print("\n✅ 验证通过!")
        return True

    def _validate_tests(self):
        """验证测试"""
        tests_dir = self.project_root / "tests"
        if not tests_dir.exists():
            self.errors.append("tests目录不存在")
            return

        unit_tests = list(tests_dir.rglob("test_*.py"))
        if not unit_tests:
            self.warnings.append("未找到单元测试")

    def _validate_imports(self):
        """验证导入"""
        app_dir = self.project_root / "app"
        if not app_dir.exists():
            self.errors.append("app目录不存在")
            return

    def _validate_config(self):
        """验证配置"""
        env_file = self.project_root / ".env"
        if not env_file.exists():
            self.errors.append(".env文件不存在")

        config_dir = self.project_root / "config"
        if not config_dir.exists():
            self.warnings.append("config目录不存在")

    def _validate_structure(self):
        """验证项目结构"""
        required_dirs = ["app", "tests", "docs", "config", "mock_service"]
        for dir_name in required_dirs:
            dir_path = self.project_root / dir_name
            if not dir_path.exists():
                self.errors.append(f"缺少必要目录: {dir_name}")

    def _validate_chat_api(self):
        """验证聊天API功能"""
        print("\n开始验证聊天API...")

        try:
            health_resp = requests.get(f"{self.api_base}/health", timeout=5)
            if health_resp.status_code != 200:
                self.errors.append(f"健康检查失败: {health_resp.status_code}")
                return
            print("  ✓ 服务健康")
        except Exception as e:
            self.errors.append(f"无法连接到服务: {e}")
            return

        test_cases = [
            {
                "name": "元数据服务-获取数据库列表",
                "message": "查看有哪些数据库",
                "expected_keywords": ["数据库", "source_db", "target_db", "databases"]
            },
            {
                "name": "元数据服务-获取表列表",
                "message": "查看source_db数据库有哪些表",
                "expected_keywords": ["表", "user_info", "product_info", "order_info", "tables"]
            },
            {
                "name": "字段映射-需求识别",
                "message": "我需要将source_db的order_info表映射到target_db的dw_order表",
                "expected_keywords": ["映射", "order_info", "dw_order", "字段", "源表", "目标表"]
            },
            {
                "name": "字段映射-CSV必须用hook",
                "message": "按照 field-mapping 技能，把 source_db.order_info 的字段结构保存为 ORDER002.csv",
                "expected_keywords": ["ORDER002", "CSV"]
            },
        ]

        for test in test_cases:
            print(f"\n测试: {test['name']}")
            try:
                full_text, events = self._chat_stream_collect(test["message"])

                found = any(kw in full_text for kw in test["expected_keywords"])
                if found:
                    print("  ✓ 响应包含关键词")
                else:
                    self.warnings.append(f"{test['name']}: 响应未包含预期关键词")
                    print(f"  ⚠ 响应: {full_text[:200]}")

                doc_errors, doc_warnings = self._validate_doc_read_before_platform_calls(events)
                if doc_errors:
                    for err in doc_errors:
                        self.errors.append(f"{test['name']}: {err}")
                if doc_warnings:
                    for warn in doc_warnings:
                        self.warnings.append(f"{test['name']}: {warn}")

                hook_errors = self._validate_no_python3_c_csv_bypass(events)
                if hook_errors:
                    for err in hook_errors:
                        self.errors.append(f"{test['name']}: {err}")

            except Exception as e:
                self.errors.append(f"{test['name']}: 请求失败 - {e}")

    def _chat_stream_collect(self, message: str):
        resp = requests.post(
            f"{self.api_base}/chat/",
            json={"message": message, "stream": True},
            stream=True,
            timeout=(5, 240),
        )
        if resp.status_code != 200:
            raise RuntimeError(f"聊天接口失败: {resp.status_code}")

        events = []
        full_text = ""
        for raw_line in resp.iter_lines(decode_unicode=True):
            if not raw_line:
                continue
            if not raw_line.startswith("data: "):
                continue
            data = raw_line[len("data: "):].strip()
            if data == "[DONE]":
                break
            payload = json.loads(data)
            events.append(payload)
            if payload.get("type") == "token":
                full_text += payload.get("content", "")

        return full_text, events

    def _validate_doc_read_before_platform_calls(self, events):
        file_reads = []
        errors = []
        warnings = []

        for ev in events:
            ev_type = ev.get("type")
            if ev_type == "file_read":
                p = ev.get("path", "")
                if p:
                    file_reads.append(p)
                continue

            if ev_type != "tool_call":
                continue
            if ev.get("name") != "platform_service":
                continue

            args = ev.get("args", {}) or {}
            doc_path = args.get("doc_path")
            doc_excerpt = args.get("doc_excerpt")
            if not doc_path or not doc_excerpt:
                errors.append("platform_service 缺少 doc_path/doc_excerpt 参数")
                continue
            if "DOC_GUARD:" not in str(doc_excerpt):
                errors.append("platform_service 的 doc_excerpt 未包含 DOC_GUARD")
                continue

            matched = any(fr.endswith(doc_path) for fr in file_reads)
            if not matched:
                warnings.append(f"未观测到 file_read 事件（可能未读取文档或前端未上报）: {doc_path}")

        return errors, warnings

    def _validate_no_python3_c_csv_bypass(self, events):
        errors = []
        for ev in events:
            if ev.get("type") != "tool_call":
                continue
            name = ev.get("name")
            if name not in {"execute", "execute_command"}:
                continue
            args = ev.get("args", {}) or {}
            cmd = str(args.get("command", ""))
            normalized = cmd.replace("\\n", " ")
            if "python3" in normalized and " -c " in normalized and "csv" in normalized and "DictWriter" in normalized:
                errors.append("检测到使用 python3 -c 生成 CSV 的绕过行为（应使用 platform_service hook）")
        return errors


def main():
    """主函数"""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    validator = TaskCompletionValidator(project_root)
    success = validator.validate()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
