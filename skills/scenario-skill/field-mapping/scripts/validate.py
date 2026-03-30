#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证结果脚本
"""

import json
import sys


def main():
    inputs = json.loads(sys.stdin.read())
    
    required_fields = ["csv_file", "mapped_csv_file", "ddl_file", "ddl_content"]
    missing_fields = [f for f in required_fields if not inputs.get(f)]
    
    if missing_fields:
        print(json.dumps({
            "success": False,
            "error": f"缺少必要字段: {', '.join(missing_fields)}"
        }, ensure_ascii=False))
        sys.exit(1)
    
    print(json.dumps({
        "success": True,
        "outputs": {}
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
