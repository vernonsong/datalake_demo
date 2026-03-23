---
name: integration-service
description: 集成任务服务。用于创建、管理和执行数据集成任务。
metadata: {"emoji":"🔄"}
---

# Integration Service

集成任务服务，用于创建、管理和执行数据集成任务。

## 服务说明

集成任务是数据平台的核心功能，用于将数据从源数据库同步到目标数据库。通过该服务可以：
- 查看已有的集成任务
- 创建新的数据集成任务
- 执行数据集成操作

## 接口列表

### 1. 获取任务列表
- **用途**: 查看已有的集成任务有哪些
- **文档**: [list-tasks.md](list-tasks.md)

### 2. 创建任务
- **用途**: 创建一个新的数据集成任务
- **文档**: [create-task.md](create-task.md)

## 使用方式

使用 platform_service 工具调用：

```
当需要查看或创建集成任务时，先阅读对应接口文档，然后调用 platform_service 工具。
```
