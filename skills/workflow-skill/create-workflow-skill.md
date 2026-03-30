# 创建工作流Skill指南

## 概述

本文档指导如何创建包含LangGraph工作流的Skill。工作流Skill将业务流程固化为可执行的工作流，避免智能体每次都需要规划和调用接口，大幅降低token消耗(96%)并提高稳定性。

## 工作流架构

```
workflow.json (配置)
    ↓
LangGraph (执行引擎)
    ↓
├─ 纯逻辑脚本 (数据处理、验证)
└─ 工具调用 (IT系统交互)
```

### 核心原则

1. **配置驱动**: 工作流定义在JSON中，无需修改代码
2. **脚本纯逻辑**: 脚本只处理数据，不调用外部系统
3. **工具解耦**: 外部系统调用通过platform_service工具+hook
4. **条件分支**: 支持基于状态的条件路由
5. **人工审批**: 支持关键节点的人工介入

## 目录结构

```
skills/scenario-skill/{workflow-name}/
├── workflow.json          # 工作流配置(必需)
├── README.md             # Skill说明文档(必需)
└── scripts/              # 纯逻辑脚本目录(可选)
    ├── script1.py
    ├── script2.py
    └── ...
```

## workflow.json 规范

### 基本结构

```json
{
  "name": "workflow-name",
  "version": "1.0.0",
  "description": "工作流描述",
  "metadata": {
    "category": "scenario",
    "author": "system",
    "created_at": "2026-03-30",
    "updated_at": "2026-03-30"
  },
  "parameters": {},
  "outputs": {},
  "nodes": [],
  "edges": [],
  "entry_point": "first_node_id"
}
```

### parameters 定义

定义工作流的输入参数：

```json
"parameters": {
  "param_name": {
    "type": "string",           // string, number, boolean, array, object
    "required": true,           // 是否必需
    "description": "参数说明",
    "enum": ["value1", "value2"], // 可选值(可选)
    "default": "default_value"   // 默认值(可选)
  }
}
```

### outputs 定义

定义工作流的输出结果：

```json
"outputs": {
  "output_name": {
    "type": "string",
    "description": "输出说明"
  }
}
```

### nodes 定义

工作流由多个节点组成，支持三种节点类型：

#### 1. script节点 - 纯逻辑脚本

```json
{
  "id": "node_id",
  "name": "节点名称",
  "type": "script",
  "script": "scripts/script_name.py",
  "progress": {
    "started": "正在执行...",
    "completed": "执行成功",
    "failed": "执行失败"
  },
  "inputs": ["input1", "input2"],
  "outputs": ["output1", "output2"]
}
```

**脚本规范**:
- 从stdin读取JSON输入
- 向stdout输出JSON结果
- 只包含纯逻辑，不调用外部系统
- 错误处理要完善

**脚本模板**:

```python
#!/usr/bin/env python3
import json
import sys

def main():
    # 读取输入
    inputs = json.loads(sys.stdin.read())
    
    # 获取参数
    param1 = inputs.get("param1")
    param2 = inputs.get("param2")
    
    try:
        # 纯逻辑处理
        result1 = process_data(param1, param2)
        result2 = calculate(result1)
        
        # 输出结果
        print(json.dumps({
            "success": True,
            "outputs": {
                "output1": result1,
                "output2": result2
            }
        }, ensure_ascii=False))
        
    except Exception as e:
        # 错误处理
        print(json.dumps({
            "success": False,
            "error": str(e)
        }, ensure_ascii=False))
        sys.exit(1)

if __name__ == "__main__":
    main()
```

#### 2. tool节点 - 工具调用

```json
{
  "id": "node_id",
  "name": "节点名称",
  "type": "tool",
  "tool": {
    "name": "platform_service",
    "params": {
      "platform": "metadata",
      "method": "GET",
      "endpoint": "/api/metadata/tables/{source_db}/{source_table}/schema",
      "doc_path": "skills/platform-skill/metadata-service/get-table-schema.md",
      "doc_excerpt": "DOC_GUARD: metadata_get_table_schema"
    }
  },
  "progress": {
    "started": "正在调用API...",
    "completed": "API调用成功",
    "failed": "API调用失败"
  },
  "inputs": ["source_db", "source_table"],
  "outputs": ["source_schema"]
}
```

**参数替换**:
- 使用 `{param_name}` 引用状态中的值
- 例如: `{source_db}` 会被替换为 `state["source_db"]`

**DOC_GUARD**:
- 必须提供 `doc_path` 或 `doc_excerpt`
- `doc_excerpt` 格式: `DOC_GUARD: hook_name`
- 防止在工具说明中泄露具体端点

#### 3. human节点 - 人工审批

```json
{
  "id": "node_id",
  "name": "节点名称",
  "type": "human",
  "progress": {
    "started": "等待人工审批",
    "completed": "审批通过",
    "failed": "审批拒绝"
  },
  "inputs": ["data_to_review", "validation_message"],
  "outputs": ["approved", "review_comment"]
}
```

**说明**:
- 工作流会在此节点暂停
- 等待人工输入审批结果
- `approved`: true/false
- `review_comment`: 审批意见

### edges 定义

定义节点之间的连接关系，支持两种边类型：

#### 1. normal边 - 普通连接

```json
{
  "from": "node1",
  "to": "node2",
  "type": "normal"
}
```

#### 2. conditional边 - 条件分支

```json
{
  "from": "check_node",
  "to": "target_node",
  "type": "conditional",
  "condition": {
    "field": "is_valid",
    "operator": "==",
    "value": true
  }
}
```

**支持的操作符**:
- `==`: 等于
- `!=`: 不等于
- `>`: 大于
- `<`: 小于
- `>=`: 大于等于
- `<=`: 小于等于
- `in`: 包含于
- `not in`: 不包含于

**多条件分支**:
同一个节点可以有多个条件边，系统会按顺序匹配，返回第一个匹配的目标节点。

**结束工作流**:
使用 `"to": "__end__"` 结束工作流。

### entry_point 定义

指定工作流的入口节点：

```json
"entry_point": "first_node_id"
```

## 完整示例

以下是一个完整的字段映射工作流示例：

```json
{
  "name": "field-mapping",
  "version": "2.0.0",
  "description": "字段映射工作流 - 将源表字段映射到目标湖表",
  "metadata": {
    "category": "scenario",
    "author": "system",
    "created_at": "2026-03-29",
    "updated_at": "2026-03-29"
  },
  "parameters": {
    "order_id": {
      "type": "string",
      "required": true,
      "description": "订单号,用于生成文件名"
    },
    "source_db": {
      "type": "string",
      "required": true,
      "description": "源数据库名"
    },
    "source_table": {
      "type": "string",
      "required": true,
      "description": "源表名"
    },
    "target_db": {
      "type": "string",
      "required": true,
      "description": "目标数据库类型",
      "enum": ["clickhouse", "hudi"]
    },
    "target_table": {
      "type": "string",
      "required": true,
      "description": "目标表名"
    }
  },
  "outputs": {
    "csv_file": {
      "type": "string",
      "description": "源表字段CSV文件路径"
    },
    "mapped_csv_file": {
      "type": "string",
      "description": "映射结果CSV文件路径"
    },
    "ddl_file": {
      "type": "string",
      "description": "DDL文件路径"
    },
    "ddl_content": {
      "type": "string",
      "description": "DDL语句内容"
    }
  },
  "nodes": [
    {
      "id": "get_source_schema",
      "name": "获取源表结构",
      "type": "tool",
      "tool": {
        "name": "platform_service",
        "params": {
          "platform": "metadata",
          "method": "GET",
          "endpoint": "/api/metadata/tables/{source_db}/{source_table}/schema",
          "doc_path": "skills/platform-skill/metadata-service/get-table-schema.md",
          "doc_excerpt": "DOC_GUARD: metadata_get_table_schema"
        }
      },
      "progress": {
        "started": "正在获取源表结构",
        "completed": "源表结构获取成功",
        "failed": "源表结构获取失败"
      },
      "inputs": ["source_db", "source_table"],
      "outputs": ["source_schema"]
    },
    {
      "id": "generate_csv",
      "name": "生成CSV文件",
      "type": "script",
      "script": "scripts/generate_csv.py",
      "progress": {
        "started": "正在生成CSV文件",
        "completed": "CSV文件生成成功",
        "failed": "CSV文件生成失败"
      },
      "inputs": ["order_id", "source_schema"],
      "outputs": ["csv_file"]
    },
    {
      "id": "check_ddl_valid",
      "name": "检查DDL是否有效",
      "type": "script",
      "script": "scripts/check_ddl_valid.py",
      "progress": {
        "started": "正在检查DDL有效性",
        "completed": "DDL检查完成",
        "failed": "DDL检查失败"
      },
      "inputs": ["ddl_content"],
      "outputs": ["is_valid", "validation_message"]
    },
    {
      "id": "human_review",
      "name": "人工审批",
      "type": "human",
      "progress": {
        "started": "等待人工审批",
        "completed": "审批通过",
        "failed": "审批拒绝"
      },
      "inputs": ["ddl_content", "validation_message"],
      "outputs": ["approved", "review_comment"]
    }
  ],
  "edges": [
    {
      "from": "get_source_schema",
      "to": "generate_csv",
      "type": "normal"
    },
    {
      "from": "check_ddl_valid",
      "to": "human_review",
      "type": "conditional",
      "condition": {
        "field": "is_valid",
        "operator": "==",
        "value": false
      }
    },
    {
      "from": "check_ddl_valid",
      "to": "validate",
      "type": "conditional",
      "condition": {
        "field": "is_valid",
        "operator": "==",
        "value": true
      }
    },
    {
      "from": "human_review",
      "to": "validate",
      "type": "conditional",
      "condition": {
        "field": "approved",
        "operator": "==",
        "value": true
      }
    },
    {
      "from": "human_review",
      "to": "__end__",
      "type": "conditional",
      "condition": {
        "field": "approved",
        "operator": "==",
        "value": false
      }
    }
  ],
  "entry_point": "get_source_schema"
}
```

## README.md 规范

每个工作流Skill必须包含README.md文档，供智能体参考：

```markdown
# {工作流名称}

## 功能描述

简要描述工作流的功能和用途。

## 使用场景

说明什么情况下应该使用这个工作流。

## 参数说明

| 参数名 | 类型 | 必需 | 说明 |
|--------|------|------|------|
| param1 | string | 是 | 参数1说明 |
| param2 | number | 否 | 参数2说明 |

## 输出说明

| 输出名 | 类型 | 说明 |
|--------|------|------|
| output1 | string | 输出1说明 |
| output2 | object | 输出2说明 |

## 工作流程

1. 步骤1: 描述
2. 步骤2: 描述
3. 步骤3: 描述

## 注意事项

- 注意事项1
- 注意事项2

## 示例

```json
{
  "workflow": "workflow-name",
  "parameters": {
    "param1": "value1",
    "param2": 123
  }
}
```
```

## 创建工作流的步骤

### 1. 分析业务流程

- 识别业务步骤
- 确定输入输出
- 识别决策点(条件分支)
- 识别需要人工介入的点

### 2. 设计节点

- **纯逻辑处理** → script节点
- **调用外部系统** → tool节点
- **需要人工确认** → human节点

### 3. 设计边

- **顺序执行** → normal边
- **条件分支** → conditional边

### 4. 编写脚本

- 遵循脚本规范
- 只包含纯逻辑
- 完善错误处理
- 添加日志输出

### 5. 编写配置

- 创建workflow.json
- 定义parameters和outputs
- 定义nodes和edges
- 设置entry_point

### 6. 编写文档

- 创建README.md
- 说明功能和用途
- 提供使用示例
- 列出注意事项

### 7. 测试验证

- 重启服务加载工作流
- 使用智能体测试
- 验证各个分支
- 验证错误处理

## 最佳实践

### 1. 脚本设计

✅ **推荐**:
```python
# 纯逻辑,易于测试
def validate_ddl(ddl_content):
    if "CREATE TABLE" not in ddl_content:
        return False, "缺少CREATE TABLE语句"
    return True, "DDL有效"
```

❌ **不推荐**:
```python
# 耦合IT系统,难以测试
def validate_ddl(ddl_content):
    response = requests.post("http://api.example.com/validate", ...)
    return response.json()
```

### 2. 工具调用

✅ **推荐**:
```json
{
  "type": "tool",
  "tool": {
    "name": "platform_service",
    "params": {
      "platform": "metadata",
      "endpoint": "/api/metadata/tables/{source_db}/{source_table}/schema",
      "doc_excerpt": "DOC_GUARD: metadata_get_table_schema"
    }
  }
}
```

❌ **不推荐**:
```json
{
  "type": "script",
  "script": "scripts/get_schema.py"
}
```
```python
# get_schema.py - 不要在脚本中调用外部系统
import requests
response = requests.get("http://api.example.com/schema")
```

### 3. 条件分支

✅ **推荐**:
```json
{
  "from": "check_amount",
  "to": "auto_approve",
  "type": "conditional",
  "condition": {
    "field": "amount",
    "operator": "<",
    "value": 10000
  }
}
```

❌ **不推荐**:
```python
# 不要在脚本中硬编码分支逻辑
if amount < 10000:
    next_node = "auto_approve"
else:
    next_node = "manual_approve"
```

### 4. 错误处理

✅ **推荐**:
```python
try:
    result = process_data(input_data)
    print(json.dumps({
        "success": True,
        "outputs": {"result": result}
    }))
except ValueError as e:
    print(json.dumps({
        "success": False,
        "error": f"数据验证失败: {str(e)}"
    }))
    sys.exit(1)
```

❌ **不推荐**:
```python
# 没有错误处理,会导致工作流异常终止
result = process_data(input_data)
print(result)
```

## 常见问题

### Q1: 如何在脚本中访问工作流参数?

A: 所有参数都通过stdin的JSON传入，使用 `inputs.get("param_name")` 获取。

### Q2: 如何在节点间传递数据?

A: 通过节点的outputs定义输出字段，这些字段会自动添加到工作流状态中，后续节点可以通过inputs引用。

### Q3: 如何调用上游系统接口?

A: 使用tool节点，配置platform_service工具，不要在script节点中直接调用。

### Q4: 如何实现复杂的条件分支?

A: 在script节点中计算条件字段，然后使用conditional边根据该字段路由。

### Q5: 如何实现循环?

A: 当前版本不支持循环，可以通过条件边回到之前的节点实现简单循环，但要注意防止死循环。

### Q6: 如何调试工作流?

A: 
1. 查看服务启动日志，确认工作流加载成功
2. 在脚本中添加日志输出到stderr
3. 使用智能体测试，观察进度消息
4. 检查工作流执行结果

## 相关文档

- [Harness规范](../../docs/harness规范.md)
- [Agent Skills技术文档](../../docs/AgentSkills技术文档.md)
- [Platform Service工具文档](../platform-skill/README.md)
- [场景Skill使用指南](../scenario-skill/README.md)

## 总结

创建工作流Skill的核心要点：

1. **配置驱动**: 一切定义在JSON中
2. **脚本纯逻辑**: 不耦合IT系统
3. **工具解耦**: 外部调用用platform_service
4. **条件分支**: 支持复杂业务逻辑
5. **人工审批**: 关键节点可介入
6. **完善文档**: 让智能体能理解和使用

遵循这些原则，可以创建稳定、高效、易维护的工作流Skill！
