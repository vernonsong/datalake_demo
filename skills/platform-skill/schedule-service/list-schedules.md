# 获取调度列表

DOC_GUARD: 4e9a1c0d7b2f43aa
REQUIRES_CONFIRMATION: false

## 说明

本接口为查询操作，不会修改系统数据，无需用户确认。

## 接口信息

- **方法**: GET
- **端点**: /api/schedules

## 调用示例

```python
platform_service(
    platform="schedule",
    method="GET",
    endpoint="/api/schedules",
    doc_path="skills/platform-skill/schedule-service/list-schedules.md",
    doc_excerpt="DOC_GUARD: 4e9a1c0d7b2f43aa"
)
```

## 返回结果

```json
{
    "schedules": [
        {"id": "1", "name": "每日报表", "cron": "0 0 * * *"}
    ]
}
```
