#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用Excel解析工具
将Excel文件转换为JSON格式，供Agent使用
"""

import pandas as pd
import json
import sys
import os


def excel_to_json(excel_path: str, sheet_name: int = 0):
    """将Excel转换为JSON数组
    
    Args:
        excel_path: Excel文件路径
        sheet_name: Sheet索引，默认0（第一个sheet）
    
    Returns:
        包含total和data的字典
    """
    try:
        if not os.path.exists(excel_path):
            raise FileNotFoundError(f"文件不存在: {excel_path}")
        
        df = pd.read_excel(excel_path, sheet_name=sheet_name)
        
        data = df.to_dict(orient='records')
        
        for row in data:
            for key in row:
                if pd.isna(row[key]):
                    row[key] = None
        
        result = {
            "total": len(data),
            "data": data
        }
        
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return result
    
    except Exception as e:
        error = {"error": str(e)}
        print(json.dumps(error, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({
            "error": "Usage: python3 excel_parser.py <excel_file> [sheet_index]"
        }, ensure_ascii=False))
        sys.exit(1)
    
    excel_path = sys.argv[1]
    sheet_name = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    
    excel_to_json(excel_path, sheet_name)
