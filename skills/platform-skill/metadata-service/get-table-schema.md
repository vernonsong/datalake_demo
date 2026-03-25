# 获取表结构

DOC_GUARD: f19b2a7c4e1d4d6f
REQUIRES_CONFIRMATION: false

## 说明

本接口为查询操作，不会修改系统数据，无需用户确认。

## 接口信息

- **方法**: GET
- **端点**: /api/metadata/schema/{database}/{table}

## 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| database | string | 是 | 数据库名称 |
| table | string | 是 | 表名称 |

## 调用示例

```python
platform_service(
    platform="metadata",
    method="GET",
    endpoint="/api/metadata/schema/source_db/orders",
    doc_path="skills/platform-skill/metadata-service/get-table-schema.md",
    doc_excerpt="DOC_GUARD: f19b2a7c4e1d4d6f"
)
```

## 返回结果

```json
{
    "columns": [
        {"name": "id", "type": "int", "comment": "订单ID"},
        {"name": "customer_id", "type": "int", "comment": "客户ID"},
        {"name": "amount", "type": "decimal", "comment": "订单金额"}
    ]
}
```
