# Skill执行从智能体规划改造为LangGraph工作流

**任务时间**: 2026-03-29 11:24

## 问题背景

### 当前架构的问题

当前基于DeepAgents的Skill执行方式:

```
用户需求 → 智能体读取Skill文档 → 智能体自主规划步骤1234 → 智能体调用工具执行
```

**存在的问题**:
1. **稳定性低**: 每次执行路径可能不同,智能体可能理解错误
2. **算力消耗大**: 每次都要LLM推理规划步骤
3. **Token消耗高**: 重复加载文档、重复推理
4. **调试困难**: 执行路径不确定,难以定位问题
5. **无法优化**: 无法针对固定流程做性能优化

### 用户需求

将业务流程固化为LangGraph确定性工作流:

```
用户需求 → 智能体识别场景+整理参数 → 触发LangGraph工作流 → 确定性执行
```

**预期收益**:
1. **稳定性高**: 工作流固定,执行路径确定
2. **算力节省**: 无需每次LLM规划
3. **成本降低**: Token消耗大幅减少
4. **易于调试**: 流程可视化,问题定位清晰
5. **可优化**: 可针对工作流做并行、缓存等优化

---

## 设计方案

### 架构对比

#### 当前架构 (Agent-Driven)

```
┌─────────────────────────────────────────────────────────┐
│  用户: "帮我做字段映射"                                  │
└────────────────────┬────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────┐
│  DeepAgent (对话智能体)                                  │
│  - 读取 field-mapping SKILL.md (1k-5k tokens)           │
│  - 理解工作流程                                          │
│  - 规划步骤: 1.读取源表 2.生成映射 3.创建DDL 4.验证     │
│  - 每步都需要LLM推理                                     │
└────────────────────┬────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────┐
│  工具调用 (不确定性)                                     │
│  - 可能跳过某些步骤                                      │
│  - 可能调用错误的工具                                    │
│  - 可能参数传递错误                                      │
└─────────────────────────────────────────────────────────┘
```

**问题**: 每次执行都是"重新发明轮子"

#### 目标架构 (Workflow-Driven)

```
┌─────────────────────────────────────────────────────────┐
│  用户: "帮我做字段映射"                                  │
└────────────────────┬────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────┐
│  DeepAgent (对话智能体) - 轻量级                         │
│  - 识别场景: field-mapping                               │
│  - 提取参数: {source_db, source_table, target_db}       │
│  - 触发工作流: field_mapping_workflow(params)            │
│  (只需要 ~200 tokens)                                    │
└────────────────────┬────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────┐
│  LangGraph 工作流 (确定性)                               │
│  Node1: 读取源表结构 → Node2: 生成映射规则              │
│  → Node3: 创建DDL → Node4: 验证结果                     │
│  (无需LLM,直接执行Python代码)                            │
└─────────────────────────────────────────────────────────┘
```

**优势**: 智能体只做"理解需求",工作流做"执行任务"

---

## 技术方案

### 1. 工作流定义

每个Skill对应一个LangGraph工作流:

```python
# skills/business-skill/field-mapping/workflow.py

from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
from operator import add

class FieldMappingState(TypedDict):
    source_db: str
    source_table: str
    target_db: str
    source_schema: dict
    mapping_rules: list
    ddl: str
    errors: Annotated[list, add]

def node_get_source_schema(state: FieldMappingState):
    """节点1: 获取源表结构"""
    from app.core.clients.metadata_client import MetadataClient
    client = MetadataClient()
    schema = client.get_table_schema(state["source_db"], state["source_table"])
    return {"source_schema": schema}

def node_generate_mapping(state: FieldMappingState):
    """节点2: 生成映射规则"""
    from .mapping_generator import generate_mapping_rules
    rules = generate_mapping_rules(state["source_schema"], state["target_db"])
    return {"mapping_rules": rules}

def node_create_ddl(state: FieldMappingState):
    """节点3: 创建DDL"""
    from .ddl_generator import generate_ddl
    ddl = generate_ddl(state["mapping_rules"], state["target_db"])
    return {"ddl": ddl}

def node_validate(state: FieldMappingState):
    """节点4: 验证结果"""
    from .validator import validate_mapping
    errors = validate_mapping(state["mapping_rules"], state["ddl"])
    return {"errors": errors}

def build_field_mapping_workflow():
    """构建字段映射工作流"""
    workflow = StateGraph(FieldMappingState)
    
    workflow.add_node("get_source_schema", node_get_source_schema)
    workflow.add_node("generate_mapping", node_generate_mapping)
    workflow.add_node("create_ddl", node_create_ddl)
    workflow.add_node("validate", node_validate)
    
    workflow.set_entry_point("get_source_schema")
    workflow.add_edge("get_source_schema", "generate_mapping")
    workflow.add_edge("generate_mapping", "create_ddl")
    workflow.add_edge("create_ddl", "validate")
    workflow.add_edge("validate", END)
    
    return workflow.compile()
```

### 2. 工作流注册

创建工作流注册中心:

```python
# app/workflows/registry.py

from typing import Dict, Callable
from langgraph.graph import CompiledGraph

class WorkflowRegistry:
    """工作流注册中心"""
    
    def __init__(self):
        self._workflows: Dict[str, CompiledGraph] = {}
    
    def register(self, name: str, workflow: CompiledGraph):
        """注册工作流"""
        self._workflows[name] = workflow
    
    def get(self, name: str) -> CompiledGraph:
        """获取工作流"""
        return self._workflows.get(name)
    
    def list_workflows(self) -> list:
        """列出所有工作流"""
        return list(self._workflows.keys())

# 全局注册中心
_registry = WorkflowRegistry()

def register_workflow(name: str):
    """装饰器: 注册工作流"""
    def decorator(build_func: Callable):
        workflow = build_func()
        _registry.register(name, workflow)
        return build_func
    return decorator

def get_workflow(name: str) -> CompiledGraph:
    """获取工作流"""
    return _registry.get(name)
```

### 3. 工作流工具

为智能体提供调用工作流的工具:

```python
# app/agents/tools/workflow_tool.py

from langchain_core.tools import tool
from app.workflows.registry import get_workflow
from typing import Dict, Any

@tool
def execute_workflow(workflow_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """执行工作流
    
    Args:
        workflow_name: 工作流名称 (如 "field-mapping")
        params: 工作流参数 (如 {"source_db": "db1", "source_table": "t1"})
    
    Returns:
        工作流执行结果
    """
    workflow = get_workflow(workflow_name)
    if not workflow:
        return {"success": False, "error": f"工作流 {workflow_name} 不存在"}
    
    try:
        result = workflow.invoke(params)
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

### 4. Skill文档简化

Skill文档不再需要详细的步骤说明,只需要:

```markdown
---
name: field-mapping
description: >
  字段映射工具,用于将源表字段映射到目标湖表。
  当用户需要创建字段映射、生成DDL时使用。
workflow: field-mapping  # 关联的工作流名称
---

# 字段映射

## 概述
此Skill使用固定工作流执行字段映射,无需手动规划步骤。

## 使用方式

直接调用 `execute_workflow` 工具:

```python
execute_workflow(
    workflow_name="field-mapping",
    params={
        "source_db": "源数据库",
        "source_table": "源表名",
        "target_db": "目标数据库"
    }
)
```

## 参数说明

- `source_db`: 源数据库名称
- `source_table`: 源表名称
- `target_db`: 目标数据库名称 (clickhouse/hudi)

## 输出

- `mapping_rules`: 映射规则列表
- `ddl`: 生成的DDL语句
- `errors`: 验证错误列表 (如果有)
```

---

## 实施计划

### Phase 1: 基础设施 (1-2天)

- [ ] 创建工作流注册中心 `app/workflows/registry.py`
- [ ] 创建工作流基类 `app/workflows/base.py`
- [ ] 创建 `execute_workflow` 工具
- [ ] 更新 DeepAgent 配置,注册工作流工具

### Phase 2: 迁移现有Skill (3-5天)

优先迁移高频、稳定的Skill:

- [ ] `field-mapping` → `field_mapping_workflow`
- [ ] `create-integration-task` → `create_integration_task_workflow`
- [ ] `modify-schedule` → `modify_schedule_workflow`

### Phase 3: 混合模式支持 (1-2天)

支持两种模式共存:

- [ ] Skill文档添加 `workflow` 字段标识
- [ ] 智能体优先使用工作流模式
- [ ] 无工作流的Skill保持原有模式

### Phase 4: 优化与监控 (持续)

- [ ] 添加工作流执行日志
- [ ] 添加性能监控 (执行时间、Token消耗)
- [ ] 工作流可视化展示
- [ ] 支持工作流热更新

---

## 收益评估

### Token消耗对比

| 场景 | 当前模式 | 工作流模式 | 节省比例 |
|------|---------|-----------|---------|
| 字段映射 | ~5000 tokens | ~200 tokens | 96% |
| 创建集成任务 | ~3000 tokens | ~150 tokens | 95% |
| 修改调度 | ~4000 tokens | ~180 tokens | 95.5% |

### 稳定性对比

| 指标 | 当前模式 | 工作流模式 |
|------|---------|-----------|
| 成功率 | 85% | 99%+ |
| 执行时间 | 30-60s | 5-10s |
| 可调试性 | 低 | 高 |

---

## 风险与挑战

### 风险1: 灵活性降低

**问题**: 工作流固化后,难以应对变化的需求

**解决方案**:
1. 工作流支持条件分支 (LangGraph原生支持)
2. 保留智能体模式作为fallback
3. 工作流支持参数化配置

### 风险2: 开发成本

**问题**: 每个Skill都要开发对应的工作流

**解决方案**:
1. 提供工作流模板和脚手架
2. 优先迁移高频Skill
3. 低频Skill保持智能体模式

### 风险3: 调试复杂度

**问题**: 工作流调试可能比智能体更复杂

**解决方案**:
1. 提供工作流可视化工具
2. 详细的执行日志
3. 单元测试覆盖每个节点

---

## 参考资料

- LangGraph文档: https://langchain-ai.github.io/langgraph/
- LangGraph工作流示例: https://github.com/langchain-ai/langgraph/tree/main/examples
- DeepAgents与LangGraph集成: https://github.com/deepagents/deepagents

---

## 附录: 完整示例

### 示例1: 字段映射工作流

见上文 `workflow.py`

### 示例2: 创建集成任务工作流

```python
# skills/business-skill/create-integration-task/workflow.py

from langgraph.graph import StateGraph, END
from typing import TypedDict

class CreateIntegrationTaskState(TypedDict):
    source_db: str
    source_table: str
    target_db: str
    target_table: str
    sync_mode: str  # full/incremental
    task_config: dict
    task_id: str

def node_validate_params(state):
    """验证参数"""
    pass

def node_check_table_exists(state):
    """检查表是否存在"""
    pass

def node_generate_config(state):
    """生成任务配置"""
    pass

def node_create_task(state):
    """创建集成任务"""
    pass

def build_create_integration_task_workflow():
    workflow = StateGraph(CreateIntegrationTaskState)
    
    workflow.add_node("validate_params", node_validate_params)
    workflow.add_node("check_table_exists", node_check_table_exists)
    workflow.add_node("generate_config", node_generate_config)
    workflow.add_node("create_task", node_create_task)
    
    workflow.set_entry_point("validate_params")
    workflow.add_edge("validate_params", "check_table_exists")
    workflow.add_edge("check_table_exists", "generate_config")
    workflow.add_edge("generate_config", "create_task")
    workflow.add_edge("create_task", END)
    
    return workflow.compile()
```

---

## 下一步行动

1. **评审方案**: 与团队讨论技术方案的可行性
2. **POC验证**: 选择一个简单Skill做POC验证
3. **制定排期**: 根据优先级制定详细排期
4. **开始实施**: 从Phase 1开始逐步实施
