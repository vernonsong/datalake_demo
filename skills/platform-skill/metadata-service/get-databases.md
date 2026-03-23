# 获取数据库列表

DOC_GUARD: 8d3f8c2e0a2b4f7a

## 接口信息

- **方法**: GET
- **端点**: /api/metadata/databases

## 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| db_type | string | 否 | 数据库类型，如 mysql、hive |

## 调用示例

```python
platform_service(
    platform="metadata",
    method="GET",
    endpoint="/api/metadata/databases",
    doc_path="skills/platform-skill/metadata-service/get-databases.md",
    doc_excerpt="DOC_GUARD: 8d3f8c2e0a2b4f7a"
)
```

## 返回结果

```json
{
    "databases": ["source_db", "target_db"]
}
```
