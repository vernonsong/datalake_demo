---
name: schedule-service
description: 调度服务。用于创建、管理和执行定时数据调度任务。
metadata: {"emoji":"⏰"}
---

# Schedule Service

调度服务，用于创建、管理和执行定时数据调度任务。

## 服务说明

调度服务是数据平台的核心功能，用于管理定时任务。通过该服务可以：
- 查看已有的调度任务
- 创建新的定时调度任务
- 更新调度任务的配置

## 接口列表

### 1. 获取调度列表
- **用途**: 查看已有的定时调度任务有哪些
- **文档**: [list-schedules.md](list-schedules.md)

### 2. 创建调度
- **用途**: 创建一个新的定时调度任务
- **文档**: [create-schedule.md](create-schedule.md)

## 使用方式

使用 platform_service 工具调用：

```
当需要查看或创建调度任务时，先阅读对应接口文档，然后调用 platform_service 工具。
```
