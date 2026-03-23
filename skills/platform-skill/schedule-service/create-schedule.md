# 创建调度

DOC_GUARD: 9b0f2a6d1c7e4e88

## 接口信息

- **方法**: POST
- **端点**: /api/schedules

## 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 是 | 调度名称 |
| cron | string | 是 | Cron表达式，如 "0 0 * * *" |
| task | object | 是 | 任务配置 |

### task 对象

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| type | string | 是 | 任务类型 |
| config | object | 是 | 任务配置 |

## 调用示例

```python
platform_service(
    platform="schedule",
    method="POST",
    endpoint="/api/schedules",
    doc_path="skills/platform-skill/schedule-service/create-schedule.md",
    doc_excerpt="DOC_GUARD: 9b0f2a6d1c7e4e88",
    json_body={
        "name": "每日数据同步",
        "cron": "0 2 * * *",
        "task": {"type": "integration", "config": {"task_id": "123"}}
    }
)
```

## 返回结果

```json
{
    "status": "success",
    "schedule_id": "456"
}
```
