#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试批量处理进度展示功能
"""

import json
from app.agents.tools.batch_tool import batch_process

# 测试数据
test_items = [
    {"单号": "ORDER101", "源库": "source_db", "源表": "order_info", "目标库": "target_db", "目标表": "dw_order"},
    {"单号": "ORDER102", "源库": "source_db", "源表": "user_info", "目标库": "target_db", "目标表": "dw_user"},
    {"单号": "ORDER103", "源库": "source_db", "源表": "product_info", "目标库": "target_db", "目标表": "dw_product"},
]

items_json = json.dumps(test_items, ensure_ascii=False)
instruction_template = "处理单号{单号}的字段映射，源库为{源库}，源表为{源表}，目标库为{目标库}，目标表为{目标表}"

print("=" * 80)
print("测试批量处理进度展示")
print("=" * 80)
print(f"\n测试数据: {len(test_items)} 个订单")
print(f"指令模板: {instruction_template}")
print("\n开始处理...\n")

# 调用批量处理工具
result = batch_process.invoke({
    "items": items_json,
    "instruction_template": instruction_template,
    "batch_size": 5
})

print("\n" + "=" * 80)
print("处理结果:")
print("=" * 80)
print(json.dumps(result, ensure_ascii=False, indent=2))
