#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
字段映射脚本
根据源表字段 CSV 和预定义映射规则，生成目标 CSV 文件和 DDL 语句
"""

import csv
import sys
import os


def load_source_fields(csv_path: str) -> list:
    """加载源表字段信息"""
    fields = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            fields.append(row)
    return fields


def load_mapping_template(template_path: str) -> dict:
    """加载映射规则模板"""
    template = {
        'source_db': '',
        'source_table': '',
        'target_db': '',
        'target_table': '',
        'type_mapping': {},
        'default_mapping_type': '直接映射'
    }
    
    if os.path.exists(template_path):
        with open(template_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # 读取第一行作为模板信息
                if not template['source_db']:
                    template['source_db'] = row.get('source_db', '')
                    template['source_table'] = row.get('source_table', '')
                    template['target_db'] = row.get('target_db', '')
                    template['target_table'] = row.get('target_table', '')
                    template['default_mapping_type'] = row.get('mapping_type', '直接映射')
                
                # 积累类型映射规则
                source_type = row.get('source_type', '')
                target_type = row.get('target_type', '')
                if source_type and target_type:
                    template['type_mapping'][source_type] = target_type
    
    return template


def get_base_name(csv_path: str) -> str:
    """获取单号（文件名不含扩展名）"""
    basename = os.path.basename(csv_path)
    name_without_ext = os.path.splitext(basename)[0]
    return name_without_ext


def generate_mappings(source_fields: list, template: dict) -> list:
    """根据源字段和模板生成完整映射"""
    mappings = []
    
    for field in source_fields:
        source_type = field.get('source_type', '')
        target_type = template['type_mapping'].get(source_type, source_type)
        
        mapping = {
            'source_db': template['source_db'],
            'source_table': template['source_table'],
            'source_field': field.get('source_field', ''),
            'source_type': source_type,
            'target_db': template['target_db'],
            'target_table': template['target_table'],
            'target_field': field.get('source_field', ''),  # 默认同名字段
            'target_type': target_type,
            'mapping_type': template['default_mapping_type']
        }
        mappings.append(mapping)
    
    return mappings


def generate_ddl(mappings: list) -> str:
    """生成 DDL 语句"""
    if not mappings:
        return "-- No mappings found"

    target_db = mappings[0]['target_db']
    target_table = mappings[0]['target_table']

    lines = [
        f"-- Target Table: {target_db}.{target_table}",
        f"CREATE TABLE IF NOT EXISTS {target_db}.{target_table} (",
    ]

    columns = []
    for m in mappings:
        if m['mapping_type'] != '忽略':
            col_def = f"    {m['target_field']} {m['target_type']}"
            columns.append(col_def)

    lines.append(',\n'.join(columns))
    lines.append(");")

    return '\n'.join(lines)


def generate_mapping_report(mappings: list) -> str:
    """生成映射报告"""
    lines = ["# 字段映射报告\n"]

    lines.append(f"## 源表：{mappings[0]['source_db']}.{mappings[0]['source_table']}")
    lines.append(f"## 目标表：{mappings[0]['target_db']}.{mappings[0]['target_table']}\n")

    lines.append("## 映射详情\n")
    lines.append("| 源字段 | 目标字段 | 类型 | 映射方式 |")
    lines.append("|--------|----------|------|----------|")

    for m in mappings:
        lines.append(f"| {m['source_field']} | {m['target_field']} | {m['source_type']} -> {m['target_type']} | {m['mapping_type']} |")

    return '\n'.join(lines)


def save_mapped_csv(mappings: list, output_path: str):
    """保存映射结果 CSV"""
    if not mappings:
        return

    fieldnames = list(mappings[0].keys())
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(mappings)


def save_ddl(ddl: str, output_path: str):
    """保存 DDL 语句"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(ddl)


def main():
    if len(sys.argv) < 2:
        print("Usage: python mapping_script.py <csv_file>")
        sys.exit(1)

    csv_path = sys.argv[1]

    if not os.path.exists(csv_path):
        print(f"Error: File not found: {csv_path}")
        sys.exit(1)

    # 加载源表字段
    source_fields = load_source_fields(csv_path)
    print(f"Loaded {len(source_fields)} source fields from {csv_path}\n")

    # 获取单号
    base_name = get_base_name(csv_path)
    output_dir = os.path.dirname(csv_path) or '.'
    
    # 加载映射规则模板
    template_path = os.path.join(os.path.dirname(__file__), '模板.csv')
    template = load_mapping_template(template_path)
    print(f"Loaded mapping template: {template['source_db']}.{template['source_table']} -> {template['target_db']}.{template['target_table']}\n")

    # 生成完整映射
    mappings = generate_mappings(source_fields, template)

    ddl = generate_ddl(mappings)
    print("=== DDL 语句 ===")
    print(ddl)
    print()

    mapped_csv_path = os.path.join(output_dir, f"{base_name}-mapped.csv")
    save_mapped_csv(mappings, mapped_csv_path)
    print(f"=== 映射结果已保存：{mapped_csv_path} ===\n")

    ddl_sql_path = os.path.join(output_dir, f"{base_name}-ddl.sql")
    save_ddl(ddl, ddl_sql_path)
    print(f"=== DDL 已保存：{ddl_sql_path} ===\n")

    report = generate_mapping_report(mappings)
    print("=== 映射报告 ===")
    print(report)
    
    print("\n=== 字段映射完成 ===")


if __name__ == "__main__":
    main()
