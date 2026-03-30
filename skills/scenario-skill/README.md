# 场景Skill目录

## 概述

场景Skill是已经固化的、经过验证的业务场景工作流。这些场景使用LangGraph工作流实现,具有以下特点:

- **确定性执行**: 固定的执行路径,无需AI规划
- **高稳定性**: 经过验证,可靠性高
- **低算力消耗**: 无需LLM推理,执行速度快
- **易于维护**: 代码化流程,便于调试和优化

## 使用原则

1. **优先使用场景Skill**: 当用户需求匹配已有场景时,直接调用场景Skill,不再让AI编排
2. **场景Skill vs 智能体编排**:
   - 场景Skill: 已知场景,固定流程,追求稳定和效率
   - 智能体编排: 新场景,灵活探索,验证后固化为场景Skill

## 场景Skill列表

### 1. field-mapping (字段映射)

**场景描述**: 将源表字段映射到目标湖表,生成DDL语句

**适用条件**:
- 用户需要创建字段映射
- 用户需要生成目标表DDL
- 用户需要查看字段映射规则

**工作流**: `field-mapping`

**使用方式**:
```python
execute_workflow("field-mapping", {
    "order_id": "ORDER001",
    "source_db": "source_db",
    "source_table": "orders",
    "target_db": "clickhouse",
    "target_table": "dw_orders"
})
```

**输出**:
- `csv_file`: 源表字段CSV文件
- `mapped_csv_file`: 映射结果CSV文件
- `ddl_file`: DDL文件路径
- `ddl_content`: DDL语句内容

---

## 添加新场景Skill

### 1. 创建工作流

在`app/workflows/`目录下创建工作流文件:

```python
# app/workflows/my_scenario_workflow.py

from langgraph.graph import StateGraph, END
from typing import TypedDict
from app.workflows.base import emit_progress
from app.workflows.registry import register_workflow

class MyScenarioState(TypedDict):
    # 定义状态字段
    pass

def node_step1(state):
    emit_progress("my-scenario", "step1", "started", {"description": "..."})
    # 执行步骤1
    emit_progress("my-scenario", "step1", "completed", {"description": "..."})
    return {}

@register_workflow("my-scenario", metadata={
    "description": "我的场景描述",
    "params": {...},
    "outputs": {...}
})
def build_my_scenario_workflow():
    workflow = StateGraph(MyScenarioState)
    workflow.add_node("step1", node_step1)
    workflow.set_entry_point("step1")
    workflow.add_edge("step1", END)
    return workflow.compile()
```

### 2. 注册工作流

在`app/workflows/loader.py`中导入新工作流:

```python
def load_all_workflows():
    from app.workflows import field_mapping_workflow
    from app.workflows import my_scenario_workflow  # 添加这行
```

### 3. 创建场景文档

在`skills/scenario-skill/`目录下创建场景文档:

```markdown
---
name: my-scenario
description: 我的场景描述
workflow: my-scenario
---

# 我的场景

## 场景说明
...

## 使用方式
...

## 参数说明
...

## 输出说明
...
```

### 4. 更新本README

在"场景Skill列表"中添加新场景的说明。

---

## 场景Skill开发规范

1. **命名规范**:
   - 工作流名称: 小写字母+连字符 (如 `field-mapping`)
   - 文件名: 下划线分隔 (如 `field_mapping_workflow.py`)

2. **进度推送**:
   - 每个节点必须发送`started`、`completed`、`failed`事件
   - 使用`emit_progress`函数发送进度

3. **错误处理**:
   - 使用`errors`字段累积错误
   - 节点失败时发送`failed`事件

4. **文档完整性**:
   - 必须包含场景说明、使用方式、参数说明、输出说明
   - 必须提供使用示例

5. **测试验证**:
   - 必须编写测试用例
   - 必须通过验证智能体验证

---

## 参考资料

- [工作流POC报告](../../docs/tasks/2026-03-29-11-24-Skill执行从智能体规划改造为LangGraph工作流-POC完成.md)
- [工作流进度推送](../../docs/tasks/2026-03-29-11-38-工作流进度实时推送功能.md)
- [LangGraph文档](https://langchain-ai.github.io/langgraph/)
