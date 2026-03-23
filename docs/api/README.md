# Mock API 接口文档

## 概述

Mock API服务整合了所有上游系统的模拟接口，用于演示数据入湖平台的完整流程。

**基础URL**: `http://localhost:5001`

---

## 目录

- [健康检查](#健康检查)
- [元数据服务](#元数据服务)
- [集成服务](#集成服务)
- [调度服务](#调度服务)
- [SQL执行服务](#sql执行服务)
- [配置中心服务](#配置中心服务)
- [大模型服务](#大模型服务)

---

## 健康检查

### GET /health

检查服务健康状态。

**响应示例**:
```json
{
  "status": "healthy",
  "service": "mock_api_server"
}
```

---

## 元数据服务

### 获取数据库列表

#### GET /api/metadata/databases

获取所有数据库列表。

**查询参数**:
| 参数 | 类型 | 描述 |
|------|------|------|
| db_type | string | 可选，按数据库类型过滤 (mysql/hive) |

**响应示例**:
```json
{
  "databases": ["source_db", "target_db"]
}
```

---

### 获取表列表

#### GET /api/metadata/tables/{database}

获取指定数据库下的所有表。

**路径参数**:
| 参数 | 描述 |
|------|------|
| database | 数据库名称 |

**响应示例**:
```json
{
  "tables": ["user_info", "product_info", "order_info"]
}
```

---

### 获取表结构

#### GET /api/metadata/schema/{database}/{table}

获取指定表的结构信息。

**路径参数**:
| 参数 | 描述 |
|------|------|
| database | 数据库名称 |
| table | 表名称 |

**响应示例**:
```json
{
  "columns": [
    {"name": "id", "type": "int"},
    {"name": "name", "type": "string"},
    {"name": "created_at", "type": "timestamp"}
  ]
}
```

---

### 请求元数据操作

#### POST /api/metadata/request

通用元数据请求接口。

**请求体**:
```json
{
  "action": "create_table",
  "database": "target_db",
  "table": "new_table",
  "columns": [...]
}
```

---

## 集成服务

### 获取任务列表

#### GET /api/integration/tasks

获取所有集成任务。

**响应示例**:
```json
{
  "tasks": [
    {
      "id": "task_1",
      "status": "success",
      "type": "full",
      "source_config": {},
      "target_config": {},
      "created_at": "2026-03-16T00:00:00"
    }
  ]
}
```

---

### 创建集成任务

#### POST /api/integration/tasks

创建新的集成任务。

**请求体**:
```json
{
  "task_type": "full",
  "source_config": {
    "database": "source_db",
    "table": "user_info"
  },
  "target_config": {
    "database": "target_db",
    "table": "dw_user"
  }
}
```

**响应示例**:
```json
{
  "task_id": "task_2",
  "status": "created"
}
```

---

## 调度服务

### 获取调度列表

#### GET /api/schedules

获取所有调度任务。

**响应示例**:
```json
{
  "schedules": [
    {
      "id": "schedule_1",
      "name": "daily_sync",
      "task_id": "task_1",
      "cron_expression": "0 0 * * *",
      "status": "active",
      "created_at": "2026-03-16T00:00:00"
    }
  ]
}
```

---

### 创建调度

#### POST /api/schedules

创建新的调度任务。

**请求体**:
```json
{
  "schedule_name": "daily_sync",
  "task_id": "task_1",
  "cron_expression": "0 0 * * *"
}
```

**响应示例**:
```json
{
  "schedule_id": "schedule_2",
  "status": "created"
}
```

---

### 更新调度

#### PUT /api/schedules/{schedule_id}

更新指定调度任务。

**路径参数**:
| 参数 | 描述 |
|------|------|
| schedule_id | 调度任务ID |

**请求体**:
```json
{
  "cron_expression": "0 8 * * *",
  "status": "active"
}
```

**响应示例**:
```json
{
  "status": "updated"
}
```

---

## SQL执行服务

### 获取执行记录

#### GET /api/sql/executions

获取所有SQL执行记录。

**响应示例**:
```json
{
  "executions": [
    {
      "id": "exec_1",
      "status": "success",
      "sql": "SELECT * FROM users",
      "database": "target_db",
      "rows_affected": 100,
      "execution_time": 0.5,
      "result": [...]
    }
  ]
}
```

---

### 执行SQL

#### POST /api/sql/execute

执行SQL语句。

**请求体**:
```json
{
  "sql": "SELECT * FROM users WHERE id > 100",
  "database": "target_db"
}
```

**响应示例**:
```json
{
  "id": "exec_2",
  "status": "success",
  "sql": "SELECT * FROM users WHERE id > 100",
  "database": "target_db",
  "rows_affected": 50,
  "execution_time": 0.3,
  "result": [
    {"id": 101, "name": "user1"},
    {"id": 102, "name": "user2"}
  ]
}
```

---

## 配置中心服务

### 获取所有配置

#### GET /api/config

获取所有配置项。

**响应示例**:
```json
{
  "configs": {
    "skill": {
      "business_path": "./skills/business",
      "platform_path": "./skills/platform",
      "scene_path": "./skills/scene",
      "temp_path": "./skills/temp"
    },
    "workflow": {
      "max_iterations": 10,
      "approval_required": true,
      "timeout_seconds": 300
    },
    "platform": {
      "metadata_api": "http://localhost:5001/api/metadata",
      "schedule_api": "http://localhost:5001/api/schedule",
      "integration_api": "http://localhost:5001/api/integration",
      "lineage_api": "http://localhost:5001/api/lineage"
    }
  }
}
```

---

### 获取单个配置

#### GET /api/config/{key}

获取指定配置项。

**路径参数**:
| 参数 | 描述 |
|------|------|
| key | 配置键名 |

**响应示例**:
```json
{
  "key": "skill",
  "value": {
    "business_path": "./skills/business",
    "platform_path": "./skills/platform"
  }
}
```

---

### 设置配置

#### POST /api/config

设置配置项。

**请求体**:
```json
{
  "key": "custom_key",
  "value": {
    "option1": "value1"
  }
}
```

**响应示例**:
```json
{
  "status": "success",
  "key": "custom_key"
}
```

---

### 更新配置

#### PUT /api/config/{key}

更新指定配置项。

**路径参数**:
| 参数 | 描述 |
|------|------|
| key | 配置键名 |

**请求体**:
```json
{
  "value": {
    "model": "qwen3.5-plus"
  }
}
```

---

### 删除配置

#### DELETE /api/config/{key}

删除指定配置项。

**路径参数**:
| 参数 | 描述 |
|------|------|
| key | 配置键名 |

**响应示例**:
```json
{
  "status": "success",
  "key": "custom_key"
}
```

---

## 错误响应

所有接口的错误响应格式如下:

```json
{
  "error": "错误信息描述"
}
```

状态码说明:
- 200: 成功
- 400: 请求参数错误
- 404: 资源不存在
- 500: 服务器内部错误
