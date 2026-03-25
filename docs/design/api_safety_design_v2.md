# 增删改接口安全保障方案 V2

## 问题回顾

### V1方案的漏洞

**攻击场景**：
```
1. 用户: "帮我看看create-integration-task这个Skill"
   → Agent读取Skill文档，获得SKILL_GUARD

2. 用户: "现在用这个接口，但是把source_table改成sensitive_table"
   → Agent已经有了SKILL_GUARD，可以调用接口
   → 绕过了Skill的约束！
```

**根本原因**：SKILL_GUARD只验证"是否基于Skill"，无法验证"是否按照Skill的意图使用"。

---

## V2方案：Skill封装调用

### 核心设计理念

**不让Agent直接调用`platform_service`，而是通过Skill提供的专用工具调用**。

```
┌─────────────────────────────────────────────┐
│  Agent                                      │
│  - 只能看到Skill提供的高层工具              │
│  - 无法直接访问platform_service             │
└──────────────────┬──────────────────────────┘
                   ↓
┌─────────────────────────────────────────────┐
│  Skill专用工具（LangChain Tool）            │
│  - create_integration_task                  │
│  - create_schedule                          │
│  - 参数验证                                 │
│  - 业务逻辑检查                             │
└──────────────────┬──────────────────────────┘
                   ↓
┌─────────────────────────────────────────────┐
│  platform_service（内部工具）               │
│  - 只能被Skill工具调用                      │
│  - 不暴露给Agent                            │
└─────────────────────────────────────────────┘
```

---

## 详细设计

### 1. Skill专用工具

#### 示例：创建集成任务工具

**文件**: `skills/business-skill/create-integration-task/tool.py`

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建集成任务专用工具
"""

from langchain_core.tools import tool
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


@tool
def create_integration_task(
    task_name: str,
    source_database: str,
    source_table: str,
    target_database: str,
    target_table: str
) -> Dict[str, Any]:
    """创建数据集成任务。
    
    本工具用于创建从源数据库到目标数据库的数据集成任务。
    
    ⚠️ 使用前提：
    1. 用户明确要求创建集成任务
    2. 已经确认源表和目标表信息
    3. 已经获得用户最终确认
    
    Args:
        task_name: 任务名称
        source_database: 源数据库名称
        source_table: 源表名称
        target_database: 目标数据库名称
        target_table: 目标表名称
    
    Returns:
        创建结果，包含task_id
    
    示例:
        create_integration_task(
            task_name="订单同步任务",
            source_database="source_db",
            source_table="orders",
            target_database="target_db",
            target_table="dw_orders"
        )
    """
    
    # 参数验证
    validation_errors = _validate_task_params(
        task_name=task_name,
        source_database=source_database,
        source_table=source_table,
        target_database=target_database,
        target_table=target_table
    )
    
    if validation_errors:
        return {
            "success": False,
            "error": f"参数验证失败: {', '.join(validation_errors)}"
        }
    
    # 业务逻辑检查
    business_check_result = _check_business_rules(
        source_database=source_database,
        source_table=source_table,
        target_database=target_database,
        target_table=target_table
    )
    
    if not business_check_result["valid"]:
        return {
            "success": False,
            "error": f"业务规则检查失败: {business_check_result['reason']}"
        }
    
    # 调用内部platform_service
    from app.agents.tools.platform_tool import _internal_platform_service
    
    result = _internal_platform_service(
        platform="integration",
        method="POST",
        endpoint="/api/integration/tasks",
        doc_path="skills/platform-skill/integration-service/create-task.md",
        doc_excerpt="DOC_GUARD: 6b2f9e1c8d0a4f53",
        skill_guard="SKILL_GUARD: a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        json_body={
            "name": task_name,
            "source": {
                "database": source_database,
                "table": source_table
            },
            "target": {
                "database": target_database,
                "table": target_table
            }
        }
    )
    
    # 记录审计日志
    _log_task_creation(
        task_name=task_name,
        source_database=source_database,
        source_table=source_table,
        target_database=target_database,
        target_table=target_table,
        result=result
    )
    
    return result


def _validate_task_params(**kwargs) -> list:
    """验证参数合法性"""
    errors = []
    
    # 检查必填参数
    for key, value in kwargs.items():
        if not value or not isinstance(value, str):
            errors.append(f"{key} 不能为空")
        elif len(value) > 100:
            errors.append(f"{key} 长度不能超过100")
    
    # 检查命名规范
    if kwargs.get("source_table"):
        if not kwargs["source_table"].isidentifier():
            errors.append("source_table 必须是有效的表名")
    
    return errors


def _check_business_rules(**kwargs) -> Dict[str, Any]:
    """检查业务规则"""
    
    # 规则1: 源表和目标表不能相同
    if (kwargs["source_database"] == kwargs["target_database"] and
        kwargs["source_table"] == kwargs["target_table"]):
        return {
            "valid": False,
            "reason": "源表和目标表不能相同"
        }
    
    # 规则2: 目标库必须是数据仓库
    if not kwargs["target_database"].startswith("dw_"):
        return {
            "valid": False,
            "reason": "目标库必须是数据仓库（以dw_开头）"
        }
    
    # 规则3: 敏感表不允许同步
    sensitive_tables = ["user_password", "user_token", "api_key"]
    if kwargs["source_table"] in sensitive_tables:
        return {
            "valid": False,
            "reason": f"敏感表 {kwargs['source_table']} 不允许同步"
        }
    
    return {"valid": True}


def _log_task_creation(**kwargs):
    """记录任务创建日志"""
    logger.info(f"创建集成任务: {kwargs}")


def get_create_integration_task_tools():
    """获取创建集成任务工具列表"""
    return [create_integration_task]
```

---

### 2. 隐藏platform_service

#### 2.1 重构platform_tool.py

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
平台服务工具 - 内部使用
"""

from typing import Optional, Dict, Any, Union
import logging

logger = logging.getLogger(__name__)


def _internal_platform_service(
    platform: str,
    method: str,
    endpoint: str,
    doc_path: str,
    doc_excerpt: str,
    skill_guard: str,
    params: Optional[Union[str, Dict]] = None,
    json_body: Optional[Union[str, Dict]] = None,
    hook: Optional[str] = None
) -> Dict[str, Any]:
    """内部平台服务调用（不暴露给Agent）
    
    本函数只能被Skill专用工具调用，不能直接暴露给Agent。
    """
    
    # ... 原有的platform_service逻辑
    
    # 安全检查
    _validate_mutation_safety(method, doc_path, skill_guard)
    
    # 调用API
    # ...
    
    # 记录审计日志
    _log_mutation_operation(...)
    
    return result


# 不再导出platform_service作为LangChain Tool
# def get_platform_tools():
#     return [platform_service]  # 删除这个
```

---

### 3. 注册Skill专用工具

#### 3.1 更新dependencies.py

```python
@lru_cache()
def get_deep_agent():
    """获取 DeepAgent 智能体（依赖注入）"""
    from deepagents import create_deep_agent
    from langgraph.checkpoint.memory import MemorySaver
    from deepagents.backends import LocalShellBackend
    from pathlib import Path

    PROJECT_ROOT = Path(__file__).parent.parent.parent

    llm = get_llm()
    checkpointer = MemorySaver()

    # 导入Skill专用工具（替代platform_service）
    from skills.business_skill.create_integration_task.tool import get_create_integration_task_tools
    from skills.business_skill.create_schedule.tool import get_create_schedule_tools
    from app.agents.tools.batch_tool import get_batch_tools
    
    skill_tools = []
    skill_tools.extend(get_create_integration_task_tools())
    skill_tools.extend(get_create_schedule_tools())
    skill_tools.extend(get_batch_tools())

    from app.core.system_prompt import SYSTEM_PROMPT

    return create_deep_agent(
        model=llm,
        system_prompt=SYSTEM_PROMPT,
        backend=LocalShellBackend(root_dir=str(PROJECT_ROOT)),
        skills=[
            str(PROJECT_ROOT / "skills/business-skill"),
            str(PROJECT_ROOT / "skills/platform-skill"),
        ],
        tools=skill_tools,  # 只注册Skill专用工具
        interrupt_on={...},
        checkpointer=checkpointer,
    )
```

---

### 4. Skill文档更新

#### 4.1 SKILL.md

```markdown
---
name: create-integration-task
description: 创建数据集成任务
metadata: {"emoji":"🔄"}
---

# 创建数据集成任务

## 工具说明

本Skill提供专用工具 `create_integration_task`，用于创建数据集成任务。

## 使用方式

```python
create_integration_task(
    task_name="订单同步任务",
    source_database="source_db",
    source_table="orders",
    target_database="dw_target",
    target_table="dw_orders"
)
```

## 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| task_name | string | 是 | 任务名称 |
| source_database | string | 是 | 源数据库名称 |
| source_table | string | 是 | 源表名称 |
| target_database | string | 是 | 目标数据库名称（必须以dw_开头） |
| target_table | string | 是 | 目标表名称 |

## 业务规则

1. 源表和目标表不能相同
2. 目标库必须是数据仓库（以dw_开头）
3. 敏感表不允许同步（user_password, user_token, api_key等）

## 安全说明

- 本工具内置参数验证和业务规则检查
- 所有操作都会记录审计日志
- 不符合业务规则的操作会被拒绝

## 使用场景

只有在以下场景下才应该调用：
1. 用户明确要求创建集成任务
2. 已经确认源表和目标表信息
3. 已经获得用户最终确认
```

---

## 安全保障

### 防御攻击场景

#### 场景1：参数篡改

```
用户: "帮我看看create-integration-task这个Skill"
→ Agent读取Skill文档

用户: "现在创建任务，但是把source_table改成user_password"
→ Agent调用 create_integration_task(source_table="user_password", ...)
→ 工具内部检查: user_password是敏感表
→ 返回错误: "业务规则检查失败: 敏感表 user_password 不允许同步"
→ ✅ 攻击被阻止
```

#### 场景2：目标库篡改

```
用户: "创建任务，目标库改成production_db"
→ Agent调用 create_integration_task(target_database="production_db", ...)
→ 工具内部检查: 目标库不是数据仓库
→ 返回错误: "业务规则检查失败: 目标库必须是数据仓库（以dw_开头）"
→ ✅ 攻击被阻止
```

#### 场景3：直接调用platform_service

```
用户: "用platform_service创建任务"
→ Agent尝试调用 platform_service(...)
→ 工具不存在（未注册）
→ 返回错误: "工具 platform_service 不存在"
→ ✅ 攻击被阻止
```

---

## 安全层级对比

### V1 vs V2

| 维度 | V1方案（SKILL_GUARD） | V2方案（Skill封装） |
|------|---------------------|-------------------|
| **防止擅自调用** | ✅ | ✅ |
| **防止参数篡改** | ❌ | ✅ |
| **业务规则检查** | ❌ | ✅ |
| **参数验证** | ❌ | ✅ |
| **实现复杂度** | 低 | 中 |
| **灵活性** | 高 | 中 |

---

## 实施步骤

### 阶段1：创建Skill专用工具（高优先级）

1. 为`create-integration-task`创建专用工具
2. 为`create-schedule`创建专用工具
3. 实现参数验证和业务规则检查

### 阶段2：重构platform_service（高优先级）

1. 将`platform_service`改为内部函数`_internal_platform_service`
2. 不再注册为LangChain Tool
3. 只允许Skill工具调用

### 阶段3：更新Agent配置（高优先级）

1. 注册Skill专用工具到DeepAgent
2. 移除platform_service的注册
3. 更新系统提示词

### 阶段4：更新Skill文档（中优先级）

1. 更新所有涉及增删改的Skill文档
2. 说明专用工具的使用方式
3. 明确业务规则和安全约束

### 阶段5：测试和验证（高优先级）

1. 测试正常使用场景
2. 测试攻击场景（参数篡改、直接调用等）
3. 验证审计日志记录

---

## 优势总结

1. **完全隔离**：Agent无法直接访问platform_service
2. **参数验证**：Skill工具内置参数验证
3. **业务规则**：强制执行业务规则，无法绕过
4. **审计完整**：所有操作都有审计日志
5. **防篡改**：即使用户诱导，也无法篡改关键参数
6. **类型安全**：工具签名明确，参数类型清晰

---

## 权衡与考虑

### 优势

- ✅ 安全性最高，无法绕过
- ✅ 业务规则集中管理
- ✅ 参数验证统一
- ✅ 审计日志完整

### 劣势

- ⚠️ 每个增删改操作需要创建专用工具
- ⚠️ 灵活性降低（但这正是安全性的来源）
- ⚠️ 维护成本增加

### 适用场景

- ✅ 高安全要求的生产环境
- ✅ 需要严格业务规则约束的场景
- ✅ 需要完整审计追溯的场景

---

## 混合方案（推荐）

### 分级管理

```
查询类操作（GET）
  → 保留platform_service，允许灵活调用

增删改操作（POST/PUT/DELETE）
  → 必须通过Skill专用工具
  → 内置参数验证和业务规则
  → 调用内部_internal_platform_service
```

### 实现方式

```python
# 查询类：保留灵活性
@tool
def query_platform_service(
    platform: str,
    endpoint: str,
    doc_path: str,
    doc_excerpt: str,
    params: Optional[Dict] = None
) -> Dict[str, Any]:
    """查询平台服务（只支持GET）"""
    
    # 只允许GET
    if method != "GET":
        return {"error": "本工具只支持查询操作（GET）"}
    
    return _internal_platform_service(
        platform=platform,
        method="GET",
        endpoint=endpoint,
        doc_path=doc_path,
        doc_excerpt=doc_excerpt,
        params=params
    )


# 增删改：强制Skill封装
# create_integration_task, create_schedule等专用工具
```

这样既保证了安全性，又保留了查询操作的灵活性！
