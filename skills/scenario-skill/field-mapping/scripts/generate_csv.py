#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成CSV文件脚本
"""

import json
import sys
import csv


def main():
    inputs = json.loads(sys.stdin.read())
    
    order_id = inputs.get("order_id")
    source_schema = inputs.get("source_schema")
    
    if not order_id or not source_schema:
        print(json.dumps({
            "success": False,
            "error": "缺少order_id或source_schema参数"
        }, ensure_ascii=False))
        sys.exit(1)
    
    try:
        csv_filename = f"{order_id}.csv"
        
        with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['source_field', 'source_type'])
            writer.writeheader()
            for col in source_schema.get('columns', []):
                writer.writerow({
                    'source_field': col['name'],
                    'source_type': col['type']
                })
        
        print(json.dumps({
            "success": True,
            "outputs": {
                "csv_file": csv_filename
            }
        }, ensure_ascii=False))
        
    except Exception as e:
        print(json.dumps({
            "success": False,
            "error": f"生成CSV文件异常: {str(e)}"
        }, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
