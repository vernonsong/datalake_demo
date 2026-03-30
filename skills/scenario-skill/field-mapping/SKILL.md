---
name: field-mapping
description: >
  字段映射场景 - 将源表字段映射到目标湖表,生成DDL语句。
  这是一个固化的场景工作流,执行稳定、速度快。
workflow: field-mapping
category: scenario
---

# 字段映射场景

## 场景说明

字段映射是数据入湖的核心场景之一。当需要将源表数据同步到数据湖时,首先需要创建字段映射关系,并生成目标表的DDL语句。

本场景使用LangGraph工作流实现,具有以下特点:
- ✅ **确定性执行**: 固定的5步流程,无需AI规划
- ✅ **高稳定性**: 经过验证,成功率99%+
- ✅ **低算力消耗**: Token消耗降低96% (5000 → 200)
- ✅ **实时进度**: 前端可实时看到执行进度

## 适用条件

当用户需求满足以下任一条件时,使用本场景:

- 用户需要创建字段映射
- 用户需要生成目标表DDL
- 用户需要查看字段映射规则
- 用户提到"字段映射"、"DDL生成"、"表结构映射"等关键词

## 使用方式

直接调用`execute_workflow`工具:

```python
execute_workflow("field-mapping", {
    "order_id": "ORDER001",
    "source_db": "source_db",
    "source_table": "orders",
    "target_db": "clickhouse",
    "target_table": "dw_orders"
})
```

## 参数说明

| 参数 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| order_id | string | 是 | 订单号,用于生成文件名 | "ORDER001" |
| source_db | string | 是 | 源数据库名 | "source_db" |
| source_table | string | 是 | 源表名 | "orders" |
| target_db | string | 是 | 目标数据库类型 | "clickhouse" 或 "hudi" |
| target_table | string | 是 | 目标表名 | "dw_orders" |

## 工作流步骤

本场景包含5个步骤,前端可实时看到执行进度:

```
1. get_source_schema    → 获取源表结构
2. generate_csv         → 生成CSV文件
3. run_mapping_script   → 运行映射脚本
4. read_ddl             → 读取DDL内容
5. validate             → 验证结果
```

### 步骤详情

#### 1. 获取源表结构
- 调用元数据服务获取源表的字段信息
- 包含字段名、类型、注释等

#### 2. 生成CSV文件
- 将源表字段信息写入CSV文件
- 文件名: `{order_id}.csv`
- 格式: `source_field,source_type`

#### 3. 运行映射脚本
- 执行`mapping_script.py`生成映射规则
- 输出映射结果CSV: `{order_id}-mapped.csv`
- 输出DDL文件: `{order_id}-ddl.sql`

#### 4. 读取DDL内容
- 读取生成的DDL文件内容
- 返回完整的DDL语句

#### 5. 验证结果
- 验证所有必要文件是否生成
- 检查是否有错误

## 输出说明

成功执行后返回:

```json
{
  "success": true,
  "data": {
    "order_id": "ORDER001",
    "source_db": "source_db",
    "source_table": "orders",
    "target_db": "clickhouse",
    "target_table": "dw_orders",
    "source_schema": {
      "columns": [...]
    },
    "csv_file": "ORDER001.csv",
    "mapped_csv_file": "ORDER001-mapped.csv",
    "ddl_file": "ORDER001-ddl.sql",
    "ddl_content": "CREATE TABLE dw_orders (...)"
  }
}
```

失败时返回:

```json
{
  "success": false,
  "error": "错误信息",
  "data": {
    "errors": ["详细错误列表"]
  }
}
```

## 前端进度展示

前端会收到`workflow_progress`事件,可以实时展示进度:

```typescript
{
  "type": "workflow_progress",
  "data": {
    "workflow": "field-mapping",
    "node": "get_source_schema",
    "status": "started",
    "data": {
      "description": "正在获取源表结构",
      "source_db": "source_db",
      "source_table": "orders"
    }
  }
}
```

建议使用步进器(Stepper)组件展示进度。

## 使用示例

### 示例1: 基本使用

```
用户: 帮我做一下ORDER001的字段映射,源表是source_db.orders,目标是clickhouse的dw_orders

智能体: 好的,我来为您执行字段映射场景。

[调用] execute_workflow("field-mapping", {
    "order_id": "ORDER001",
    "source_db": "source_db",
    "source_table": "orders",
    "target_db": "clickhouse",
    "target_table": "dw_orders"
})

[进度] 正在获取源表结构...
[进度] 正在生成CSV文件...
[进度] 正在运行映射脚本...
[进度] 正在读取DDL内容...
[进度] 验证通过,工作流执行完成

智能体: ✅ 字段映射已完成!

生成的文件:
- 源表字段: ORDER001.csv
- 映射结果: ORDER001-mapped.csv
- DDL文件: ORDER001-ddl.sql

DDL内容:
```sql
CREATE TABLE dw_orders (
    order_id Int64,
    customer_id Int64,
    order_date Date,
    amount Decimal(10,2)
) ENGINE = MergeTree()
ORDER BY order_id;
```
```

### 示例2: 错误处理

```
用户: 帮我做字段映射,源表是test_db.not_exist

智能体: 好的,我来为您执行字段映射场景。

[调用] execute_workflow("field-mapping", {...})

[进度] 正在获取源表结构...
[错误] 源表结构获取失败: 表不存在

智能体: ❌ 字段映射失败

错误信息: 源表 test_db.not_exist 不存在,请检查表名是否正确。
```

## 性能指标

| 指标 | 智能体模式 | 工作流模式 | 提升 |
|------|-----------|-----------|------|
| Token消耗 | ~5000 | ~200 | 96%↓ |
| 执行时间 | 30-60s | 5-10s | 83%↓ |
| 成功率 | 85% | 99%+ | 14%↑ |

## 注意事项

1. **订单号唯一性**: order_id必须唯一,避免文件覆盖
2. **表名正确性**: 确保源表存在且有访问权限
3. **目标数据库**: 目前支持clickhouse和hudi
4. **文件清理**: 执行完成后建议清理临时CSV文件

## 相关文档

- [工作流POC报告](../../../docs/tasks/2026-03-29-11-24-Skill执行从智能体规划改造为LangGraph工作流-POC完成.md)
- [工作流进度推送](../../../docs/tasks/2026-03-29-11-38-工作流进度实时推送功能.md)
- [映射脚本说明](../../business-skill/field-mapping/mapping_script.py)

## 版本历史

- v1.0.0 (2026-03-29): 初始版本,从business-skill迁移为scenario-skill
