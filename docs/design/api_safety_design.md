# 增删改接口安全保障方案

## 问题背景

平台提供了`platform_service`工具，支持调用各种API接口，包括：
- **查询类**（GET）：相对安全，只读操作
- **增删改类**（POST/PUT/DELETE）：高风险，可能造成数据变更

**核心风险**：
1. Agent可能在没有明确Skill指导的情况下，擅自调用增删改接口
2. 用户可能通过对话诱导Agent执行危险操作
3. 缺少审计和追溯机制

## 设计目标

1. **强制Skill约束**：增删改接口必须基于已存在的Skill调用
2. **多层防护**：从工具层、Skill层、验证层多重保障
3. **可审计**：所有增删改操作可追溯
4. **用户友好**：不影响正常使用体验

---

## 解决方案

### 方案架构

```
┌─────────────────────────────────────────────┐
│  第1层：工具层安全检查                       │
│  - HTTP方法白名单                            │
│  - Skill授权标记验证                         │
│  - DOC_GUARD验证                             │
└──────────────────┬──────────────────────────┘
                   ↓
┌─────────────────────────────────────────────┐
│  第2层：Skill层约束                          │
│  - 增删改接口必须在Skill中明确声明           │
│  - Skill文档包含SKILL_GUARD标记              │
│  - 接口文档包含MUTATION_GUARD标记            │
└──────────────────┬──────────────────────────┘
                   ↓
┌─────────────────────────────────────────────┐
│  第3层：审计日志                             │
│  - 记录所有增删改操作                        │
│  - 包含调用来源、参数、结果                  │
└─────────────────────────────────────────────┘
```

---

## 详细设计

### 1. 工具层安全检查

#### 1.1 增强`platform_service`工具

在`app/agents/tools/platform_tool.py`中增加安全检查：

```python
def _validate_mutation_safety(
    method: str,
    doc_path: str,
    skill_guard: Optional[str] = None
) -> None:
    """验证增删改操作的安全性"""
    
    # 定义危险方法
    MUTATION_METHODS = ["POST", "PUT", "DELETE", "PATCH"]
    
    if method.upper() not in MUTATION_METHODS:
        return  # 查询类操作，直接通过
    
    # 增删改操作必须提供skill_guard
    if not skill_guard:
        raise ValueError(
            f"增删改操作（{method}）必须提供 skill_guard 参数。\n"
            f"skill_guard 应从对应 Skill 文档中复制，格式: SKILL_GUARD: <uuid>"
        )
    
    # 验证skill_guard格式
    if not skill_guard.startswith("SKILL_GUARD:"):
        raise ValueError("skill_guard 必须以 'SKILL_GUARD:' 开头")
    
    # 验证接口文档是否包含MUTATION_GUARD
    resolved = _resolve_doc_path(doc_path)
    content = resolved.read_text(encoding="utf-8")
    
    if "MUTATION_GUARD:" not in content:
        raise ValueError(
            f"接口文档 {doc_path} 缺少 MUTATION_GUARD 标记。\n"
            f"增删改接口必须在文档中明确标记为可变更操作。"
        )
    
    # 验证skill_guard是否在对应的Skill文档中存在
    skill_doc_path = _extract_skill_doc_path(doc_path)
    if skill_doc_path:
        skill_content = skill_doc_path.read_text(encoding="utf-8")
        if skill_guard not in skill_content:
            raise ValueError(
                f"skill_guard 未在 Skill 文档中找到。\n"
                f"请确保从正确的 Skill 文档中复制 skill_guard。"
            )
```

#### 1.2 更新工具签名

```python
@tool
def platform_service(
    platform: str,
    method: str,
    endpoint: str,
    doc_path: str,
    doc_excerpt: str,
    skill_guard: Optional[str] = None,  # 新增参数
    params: Optional[Union[str, Dict]] = None,
    json_body: Optional[Union[str, Dict]] = None,
    hook: Optional[str] = None
) -> Dict[str, Any]:
    """调用平台服务API的工具。
    
    ⚠️ 安全约束：
    - 查询操作（GET）：只需提供 doc_path 和 doc_excerpt
    - 增删改操作（POST/PUT/DELETE）：必须额外提供 skill_guard
    
    Args:
        ...
        skill_guard: Skill授权标记（增删改操作必填），从Skill文档复制
        ...
    """
    
    # 安全检查
    try:
        _validate_mutation_safety(
            method=method,
            doc_path=doc_path,
            skill_guard=skill_guard
        )
    except Exception as e:
        return {
            "success": False,
            "error": f"安全检查失败: {str(e)}"
        }
    
    # ... 原有逻辑
```

---

### 2. Skill层约束

#### 2.1 Skill文档规范

每个涉及增删改操作的Skill必须：

1. **在SKILL.md中声明SKILL_GUARD**

```markdown
---
name: create-integration-task
description: 创建数据集成任务
metadata: {"emoji":"🔄"}
---

# 创建数据集成任务

SKILL_GUARD: a1b2c3d4-e5f6-7890-abcd-ef1234567890

## 安全说明

本Skill涉及创建操作，需要谨慎使用。只有在以下场景下才应该调用：
1. 用户明确要求创建集成任务
2. 已经确认源表和目标表信息
3. 已经获得用户最终确认

## 工作流程

...
```

2. **在接口文档中声明MUTATION_GUARD**

```markdown
# 创建任务

DOC_GUARD: 6b2f9e1c8d0a4f53
MUTATION_GUARD: POST

## 安全警告

⚠️ 本接口会创建新的集成任务，请确保：
- 已经验证源表和目标表存在
- 已经获得用户确认
- 参数配置正确

## 接口信息

- **方法**: POST
- **端点**: /api/integration/tasks

...

## 调用示例

```python
platform_service(
    platform="integration",
    method="POST",
    endpoint="/api/integration/tasks",
    doc_path="skills/platform-skill/integration-service/create-task.md",
    doc_excerpt="DOC_GUARD: 6b2f9e1c8d0a4f53",
    skill_guard="SKILL_GUARD: a1b2c3d4-e5f6-7890-abcd-ef1234567890",  # 必须提供
    json_body={...}
)
```
```

#### 2.2 Skill目录结构

```
skills/business-skill/
├── create-integration-task/
│   ├── SKILL.md              # 包含SKILL_GUARD
│   └── validation.py         # 可选的参数验证
├── update-schedule/
│   ├── SKILL.md              # 包含SKILL_GUARD
│   └── validation.py
└── field-mapping/            # 只读操作，无需SKILL_GUARD
    └── SKILL.md
```

---

### 3. 审计日志

#### 3.1 审计日志记录

在`platform_service`工具中增加审计日志：

```python
import logging
from datetime import datetime

audit_logger = logging.getLogger("audit")

def _log_mutation_operation(
    platform: str,
    method: str,
    endpoint: str,
    doc_path: str,
    skill_guard: str,
    params: Optional[Dict],
    json_body: Optional[Dict],
    result: Dict,
    thread_id: Optional[str] = None
):
    """记录增删改操作的审计日志"""
    
    audit_entry = {
        "timestamp": datetime.now().isoformat(),
        "thread_id": thread_id,
        "operation": {
            "platform": platform,
            "method": method,
            "endpoint": endpoint
        },
        "authorization": {
            "doc_path": doc_path,
            "skill_guard": skill_guard
        },
        "request": {
            "params": params,
            "body": json_body
        },
        "response": {
            "success": result.get("success", True),
            "status": result.get("status")
        }
    }
    
    audit_logger.info(json.dumps(audit_entry, ensure_ascii=False))
```

#### 3.2 审计日志配置

在`app/core/logging_config.py`中配置审计日志：

```python
LOGGING_CONFIG = {
    "version": 1,
    "handlers": {
        "audit_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "logs/audit.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 10,
            "formatter": "json"
        }
    },
    "loggers": {
        "audit": {
            "handlers": ["audit_file"],
            "level": "INFO",
            "propagate": False
        }
    }
}
```

---

### 4. 验证器增强

#### 4.1 验证器检查

在`scripts/task_completion_validator.py`中增加检查：

```python
def validate_mutation_operations(events: List[Dict]) -> List[str]:
    """验证增删改操作是否符合安全规范"""
    
    errors = []
    
    # 提取所有platform_service调用
    tool_calls = [e for e in events if e.get("type") == "tool_call" 
                  and e.get("tool") == "platform_service"]
    
    for call in tool_calls:
        args = call.get("args", {})
        method = args.get("method", "").upper()
        
        # 检查增删改操作
        if method in ["POST", "PUT", "DELETE", "PATCH"]:
            # 必须提供skill_guard
            if not args.get("skill_guard"):
                errors.append(
                    f"增删改操作（{method} {args.get('endpoint')}）"
                    f"缺少 skill_guard 参数"
                )
            
            # 必须先读取Skill文档
            doc_path = args.get("doc_path", "")
            skill_doc_path = extract_skill_doc_path(doc_path)
            
            if skill_doc_path:
                # 检查是否读取了Skill文档
                skill_reads = [e for e in events 
                              if e.get("type") == "file_read" 
                              and skill_doc_path in e.get("path", "")]
                
                if not skill_reads:
                    errors.append(
                        f"增删改操作（{method} {args.get('endpoint')}）"
                        f"未读取对应的 Skill 文档: {skill_doc_path}"
                    )
    
    return errors
```

---

## 使用示例

### 正确的使用方式

#### 场景：创建集成任务

```python
# 步骤1: Agent读取Skill文档
read_file("skills/business-skill/create-integration-task/SKILL.md")

# 步骤2: Agent读取接口文档
read_file("skills/platform-skill/integration-service/create-task.md")

# 步骤3: Agent调用接口（携带skill_guard）
platform_service(
    platform="integration",
    method="POST",
    endpoint="/api/integration/tasks",
    doc_path="skills/platform-skill/integration-service/create-task.md",
    doc_excerpt="DOC_GUARD: 6b2f9e1c8d0a4f53",
    skill_guard="SKILL_GUARD: a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    json_body={
        "name": "订单同步任务",
        "source": {"database": "source_db", "table": "orders"},
        "target": {"database": "target_db", "table": "orders"}
    }
)
```

### 错误的使用方式

#### 错误1：缺少skill_guard

```python
platform_service(
    platform="integration",
    method="POST",  # 增删改操作
    endpoint="/api/integration/tasks",
    doc_path="skills/platform-skill/integration-service/create-task.md",
    doc_excerpt="DOC_GUARD: 6b2f9e1c8d0a4f53",
    # ❌ 缺少 skill_guard
    json_body={...}
)

# 返回错误：
# {
#   "success": False,
#   "error": "安全检查失败: 增删改操作（POST）必须提供 skill_guard 参数"
# }
```

#### 错误2：skill_guard不匹配

```python
platform_service(
    platform="integration",
    method="POST",
    endpoint="/api/integration/tasks",
    doc_path="skills/platform-skill/integration-service/create-task.md",
    doc_excerpt="DOC_GUARD: 6b2f9e1c8d0a4f53",
    skill_guard="SKILL_GUARD: wrong-uuid",  # ❌ 错误的skill_guard
    json_body={...}
)

# 返回错误：
# {
#   "success": False,
#   "error": "安全检查失败: skill_guard 未在 Skill 文档中找到"
# }
```

---

## 安全层级对比

| 层级 | 检查项 | 查询操作 | 增删改操作 |
|------|--------|----------|-----------|
| **工具层** | HTTP方法 | ✅ 允许 | ⚠️ 需额外检查 |
| **工具层** | DOC_GUARD | ✅ 必需 | ✅ 必需 |
| **工具层** | SKILL_GUARD | ❌ 不需要 | ✅ 必需 |
| **工具层** | MUTATION_GUARD | ❌ 不需要 | ✅ 必需 |
| **Skill层** | Skill文档存在 | ❌ 可选 | ✅ 必需 |
| **审计层** | 操作日志 | ❌ 不记录 | ✅ 必需记录 |

---

## 实施步骤

### 阶段1：工具层增强（高优先级）

1. 修改`platform_tool.py`，增加`skill_guard`参数
2. 实现`_validate_mutation_safety`函数
3. 增加审计日志记录

### 阶段2：Skill文档规范（高优先级）

1. 为所有增删改Skill添加`SKILL_GUARD`
2. 为所有增删改接口文档添加`MUTATION_GUARD`
3. 更新调用示例

### 阶段3：验证器增强（中优先级）

1. 修改`task_completion_validator.py`
2. 增加增删改操作的安全检查
3. 增加测试用例

### 阶段4：审计和监控（低优先级）

1. 配置审计日志
2. 实现审计日志查询工具
3. 增加告警机制

---

## 优势总结

1. **多层防护**：工具层、Skill层、验证层三重保障
2. **强制约束**：增删改操作必须基于Skill，无法绕过
3. **可追溯**：所有操作有审计日志，可回溯
4. **向后兼容**：查询操作不受影响，只增强增删改操作
5. **用户友好**：错误提示清晰，指导正确使用

---

## 后续优化

1. **权限分级**：不同Skill有不同的权限级别
2. **用户确认**：高风险操作需要用户二次确认
3. **回滚机制**：支持操作回滚
4. **审计查询**：提供审计日志查询界面
5. **告警通知**：异常操作实时告警
