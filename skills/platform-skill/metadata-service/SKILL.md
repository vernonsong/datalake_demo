---
name: metadata-service
description: 元数据服务。用于查询和管理数据库、表结构等元数据信息。
metadata: {"emoji":"📦"}
---

# Metadata Service

元数据服务，提供数据库和表结构的查询能力。

## 服务说明

元数据服务是数据平台的核心组件，用于管理所有数据库和表的元信息。通过该服务可以：
- 查询有哪些数据库
- 查询某个数据库下有哪些表
- 查询表的字段结构（列名、类型、注释等）

## 接口列表

### 1. 获取数据库列表
- **用途**: 查看数据平台中有哪些数据库
- **文档**: [get-databases.md](get-databases.md)

### 2. 获取表列表
- **用途**: 查看某个数据库下有哪些表
- **文档**: [get-tables.md](get-tables.md)

### 3. 获取表结构
- **用途**: 查看表有哪些字段，字段类型是什么
- **文档**: [get-table-schema.md](get-table-schema.md)

## 使用方式

使用 platform_service 工具调用：

```
当需要查询数据库信息时，先阅读对应接口文档，然后调用 platform_service 工具。
```
