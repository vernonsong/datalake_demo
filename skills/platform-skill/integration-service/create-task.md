# 创建任务

DOC_GUARD: 6b2f9e1c8d0a4f53
REQUIRES_CONFIRMATION: true

## 安全警告

⚠️ 本接口会创建新的数据集成任务，需要用户确认。

变更内容：
- 创建新的数据集成任务
- 任务创建后将开始数据同步

请确保：
- 源表和目标表信息正确
- 已获得用户授权

## 接口信息

- **方法**: POST
- **端点**: /api/integration/tasks

## 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 是 | 任务名称 |
| source | object | 是 | 源数据库配置 |
| target | object | 是 | 目标数据库配置 |

### source/target 对象

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| database | string | 是 | 数据库名称 |
| table | string | 是 | 表名称 |

## 调用示例

```python
platform_service(
    platform="integration",
    method="POST",
    endpoint="/api/integration/tasks",
    doc_path="skills/platform-skill/integration-service/create-task.md",
    doc_excerpt="DOC_GUARD: 6b2f9e1c8d0a4f53",
    json_body={
        "name": "订单同步任务",
        "source": {"database": "source_db", "table": "orders"},
        "target": {"database": "target_db", "table": "orders"}
    }
)
```

## 返回结果

```json
{
    "status": "success",
    "task_id": "123"
}
```
