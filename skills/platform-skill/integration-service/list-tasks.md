# 获取任务列表

DOC_GUARD: 7a0c1d9e3b5f4a22

## 接口信息

- **方法**: GET
- **端点**: /api/integration/tasks

## 调用示例

```python
platform_service(
    platform="integration",
    method="GET",
    endpoint="/api/integration/tasks",
    doc_path="skills/platform-skill/integration-service/list-tasks.md",
    doc_excerpt="DOC_GUARD: 7a0c1d9e3b5f4a22"
)
```

## 返回结果

```json
{
    "tasks": [
        {"id": "1", "name": "订单同步", "source": "source_db", "target": "target_db"}
    ]
}
```
