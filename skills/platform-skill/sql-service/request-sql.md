# 提交SQL请求

DOC_GUARD: 8f3e2d1c4b5a6970
REQUIRES_CONFIRMATION: true

## 说明

提交一个SQL请求到服务端。
此操作会修改服务器状态（提交请求），因此需要用户确认。

## 接口信息

- **方法**: POST
- **端点**: /api/sql/request

## 参数说明

请求体为JSON格式，包含以下字段：

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| sql | string | 是 | 要执行的SQL语句 |
| database | string | 否 | 目标数据库 |

## 调用示例

```python
platform_service(
    platform="sql",
    method="POST",
    endpoint="/api/sql/request",
    doc_path="skills/platform-skill/sql-service/request-sql.md",
    doc_excerpt="DOC_GUARD: 8f3e2d1c4b5a6970",
    json_body={
        "sql": "SELECT * FROM users",
        "database": "main_db"
    }
)
```

## 返回结果

```json
{
    "status": "success",
    "data": {
        "sql": "SELECT * FROM users",
        "database": "main_db"
    }
}
```
