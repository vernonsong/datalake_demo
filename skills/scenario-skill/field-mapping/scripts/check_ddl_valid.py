#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查DDL有效性脚本 - 纯逻辑,不耦合IT系统
"""

import json
import sys
import re


def main():
    inputs = json.loads(sys.stdin.read())
    
    ddl_content = inputs.get("ddl_content", "")
    
    if not ddl_content:
        print(json.dumps({
            "success": True,
            "outputs": {
                "is_valid": False,
                "validation_message": "DDL内容为空"
            }
        }, ensure_ascii=False))
        return
    
    issues = []
    
    if "CREATE TABLE" not in ddl_content.upper():
        issues.append("缺少CREATE TABLE语句")
    
    if not re.search(r'ENGINE\s*=', ddl_content, re.IGNORECASE):
        issues.append("缺少ENGINE定义")
    
    if not re.search(r'ORDER\s+BY', ddl_content, re.IGNORECASE):
        issues.append("缺少ORDER BY定义")
    
    if len(ddl_content) < 50:
        issues.append("DDL内容过短,可能不完整")
    
    is_valid = len(issues) == 0
    
    if is_valid:
        validation_message = "DDL格式检查通过"
    else:
        validation_message = f"DDL存在以下问题: {'; '.join(issues)}"
    
    print(json.dumps({
        "success": True,
        "outputs": {
            "is_valid": is_valid,
            "validation_message": validation_message
        }
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
