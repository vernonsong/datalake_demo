# 获取表列表

DOC_GUARD: 2c1a6f7b9d5e4c13
REQUIRES_CONFIRMATION: false

## 说明

本接口为查询操作，不会修改系统数据，无需用户确认。

## 接口信息

- **方法**: GET
- **端点**: /api/metadata/tables/{database}

## 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| database | string | 是 | 数据库名称 |

## 调用示例

```python
platform_service(
    platform="metadata",
    method="GET",
    endpoint="/api/metadata/tables/source_db",
    doc_path="skills/platform-skill/metadata-service/get-tables.md",
    doc_excerpt="DOC_GUARD: 2c1a6f7b9d5e4c13"
)
```

## 返回结果

```json
{
    "tables": ["orders", "customers", "products"]
}
```
