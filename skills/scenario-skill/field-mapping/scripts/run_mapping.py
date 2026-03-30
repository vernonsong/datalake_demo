#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
运行映射脚本
"""

import json
import sys
import subprocess
import os


def main():
    inputs = json.loads(sys.stdin.read())
    
    csv_file = inputs.get("csv_file")
    order_id = inputs.get("order_id")
    
    if not csv_file or not order_id:
        print(json.dumps({
            "success": False,
            "error": "缺少csv_file或order_id参数"
        }, ensure_ascii=False))
        sys.exit(1)
    
    if not os.path.exists(csv_file):
        print(json.dumps({
            "success": False,
            "error": f"CSV文件不存在: {csv_file}"
        }, ensure_ascii=False))
        sys.exit(1)
    
    try:
        script_path = "skills/business-skill/field-mapping/mapping_script.py"
        
        result = subprocess.run(
            ["python3", script_path, csv_file],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            print(json.dumps({
                "success": False,
                "error": f"映射脚本执行失败: {result.stderr}"
            }, ensure_ascii=False))
            sys.exit(1)
        
        mapped_csv = f"{order_id}-mapped.csv"
        ddl_file = f"{order_id}-ddl.sql"
        
        if not os.path.exists(mapped_csv):
            print(json.dumps({
                "success": False,
                "error": f"映射结果文件未生成: {mapped_csv}"
            }, ensure_ascii=False))
            sys.exit(1)
        
        if not os.path.exists(ddl_file):
            print(json.dumps({
                "success": False,
                "error": f"DDL文件未生成: {ddl_file}"
            }, ensure_ascii=False))
            sys.exit(1)
        
        print(json.dumps({
            "success": True,
            "outputs": {
                "mapped_csv_file": mapped_csv,
                "ddl_file": ddl_file
            }
        }, ensure_ascii=False))
        
    except subprocess.TimeoutExpired:
        print(json.dumps({
            "success": False,
            "error": "映射脚本执行超时(30s)"
        }, ensure_ascii=False))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({
            "success": False,
            "error": f"运行映射脚本异常: {str(e)}"
        }, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
