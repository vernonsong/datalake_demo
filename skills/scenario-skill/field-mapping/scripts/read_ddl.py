#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
读取DDL内容脚本
"""

import json
import sys
import os


def main():
    inputs = json.loads(sys.stdin.read())
    
    ddl_file = inputs.get("ddl_file")
    
    if not ddl_file:
        print(json.dumps({
            "success": False,
            "error": "缺少ddl_file参数"
        }, ensure_ascii=False))
        sys.exit(1)
    
    if not os.path.exists(ddl_file):
        print(json.dumps({
            "success": False,
            "error": f"DDL文件不存在: {ddl_file}"
        }, ensure_ascii=False))
        sys.exit(1)
    
    try:
        with open(ddl_file, 'r', encoding='utf-8') as f:
            ddl_content = f.read()
        
        print(json.dumps({
            "success": True,
            "outputs": {
                "ddl_content": ddl_content
            }
        }, ensure_ascii=False))
        
    except Exception as e:
        print(json.dumps({
            "success": False,
            "error": f"读取DDL文件异常: {str(e)}"
        }, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
