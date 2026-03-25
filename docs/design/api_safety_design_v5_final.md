# 增删改接口安全保障方案 V5（最终方案 - 基于文档标记）

## 问题回顾

V4方案的问题：仅凭HTTP方法判断是否需要确认不够准确，因为：
- 很多查询接口也使用POST方法（如复杂查询、批量查询）
- 无法区分真正的数据变更操作和查询操作

## V5方案：基于文档标记

### 核心设计

在接口文档中明确标记是否需要用户确认，通过`REQUIRES_CONFIRMATION`标记。

---

## 详细设计

### 1. 接口文档规范

#### 1.1 需要确认的接口

**示例**: `skills/platform-skill/integration-service/create-task.md`

```markdown
# 创建集成任务

DOC_GUARD: 6b2f9e1c8d0a4f53
REQUIRES_CONFIRMATION: true

## 安全警告

⚠️ 本接口会创建新的数据集成任务，需要用户确认。

## 接口信息

- **方法**: POST
- **端点**: /api/integration/tasks
- **说明**: 创建数据集成任务

## 请求参数

...
```

#### 1.2 不需要确认的接口（包括POST查询）

**示例**: `skills/platform-skill/metadata-service/batch-query-schema.md`

```markdown
# 批量查询表结构

DOC_GUARD: a1b2c3d4e5f6
REQUIRES_CONFIRMATION: false

## 接口信息

- **方法**: POST
- **端点**: /api/metadata/batch-query
- **说明**: 批量查询多个表的结构信息（使用POST是因为参数较多）

## 请求参数

...
```

---

### 2. 动态中断判断函数

#### 2.1 实现_should_interrupt_platform_service

**文件**: `app/core/dependencies.py`

```python
from pathlib import Path
import re

def _should_interrupt_platform_service(tool_call: dict) -> bool:
    """判断platform_service调用是否需要中断
    
    通过读取接口文档中的REQUIRES_CONFIRMATION标记来判断
    
    Args:
        tool_call: 工具调用信息，包含args等
    
    Returns:
        True: 需要中断（需要用户确认）
        False: 不需要中断（不需要确认）
    """
    args = tool_call.get("args", {})
    doc_path = args.get("doc_path", "")
    
    if not doc_path:
        # 没有提供doc_path，默认不中断（但这种情况不应该发生）
        return False
    
    # 解析doc_path
    try:
        resolved_path = _resolve_doc_path(doc_path)
        
        # 读取文档内容
        content = resolved_path.read_text(encoding="utf-8")
        
        # 查找REQUIRES_CONFIRMATION标记
        match = re.search(r'REQUIRES_CONFIRMATION:\s*(true|false)', content, re.IGNORECASE)
        
        if match:
            requires_confirmation = match.group(1).lower() == 'true'
            return requires_confirmation
        else:
            # 没有找到标记，默认不需要确认
            # 这样可以向后兼容，旧的文档不需要立即更新
            return False
    
    except Exception as e:
        # 读取文档失败，为了安全起见，默认需要确认
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"读取接口文档失败: {doc_path}, 错误: {e}")
        return True  # 安全起见，默认需要确认


def _resolve_doc_path(doc_path: str) -> Path:
    """解析文档路径"""
    from pathlib import Path
    
    PROJECT_ROOT = Path(__file__).parent.parent.parent
    
    # 支持相对路径和绝对路径
    if doc_path.startswith('/'):
        resolved = Path(doc_path)
    else:
        resolved = PROJECT_ROOT / doc_path
    
    if not resolved.exists():
        raise FileNotFoundError(f"接口文档不存在: {resolved}")
    
    return resolved


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

    from app.agents.tools.platform_tool import get_platform_tools
    from app.agents.tools.batch_tool import get_batch_tools
    
    platform_tools = get_platform_tools()
    batch_tools = get_batch_tools()

    from app.core.system_prompt import SYSTEM_PROMPT

    return create_deep_agent(
        model=llm,
        system_prompt=SYSTEM_PROMPT,
        backend=LocalShellBackend(root_dir=str(PROJECT_ROOT)),
        skills=[
            str(PROJECT_ROOT / "skills/business-skill"),
            str(PROJECT_ROOT / "skills/platform-skill"),
        ],
        tools=platform_tools + batch_tools,
        interrupt_on={
            "write_file": True,
            "read_file": False,
            "edit_file": False,
            "execute_command": False,
            "create_directory": False,
            "platform_service": _should_interrupt_platform_service,  # 基于文档标记判断
        },
        checkpointer=checkpointer,
    )
```

---

### 3. 接口文档分类

#### 3.1 需要确认的接口（REQUIRES_CONFIRMATION: true）

| 接口 | 方法 | 说明 |
|------|------|------|
| 创建集成任务 | POST | 创建新的数据集成任务 |
| 更新调度配置 | PUT | 修改调度配置 |
| 删除任务 | DELETE | 删除集成任务 |
| 启动任务 | POST | 启动数据同步任务 |
| 停止任务 | POST | 停止数据同步任务 |

#### 3.2 不需要确认的接口（REQUIRES_CONFIRMATION: false）

| 接口 | 方法 | 说明 |
|------|------|------|
| 查询表结构 | GET | 查询单个表的结构 |
| 批量查询表结构 | POST | 批量查询多个表（POST因为参数多） |
| 查询任务列表 | GET | 查询集成任务列表 |
| 查询任务详情 | GET | 查询单个任务详情 |
| 查询任务状态 | POST | 批量查询任务状态（POST因为参数多） |

---

### 4. 文档标记规范

#### 4.1 标记位置

`REQUIRES_CONFIRMATION`标记应该放在文档开头，紧跟在`DOC_GUARD`之后：

```markdown
# 接口名称

DOC_GUARD: <uuid>
REQUIRES_CONFIRMATION: true|false

## 接口信息
...
```

#### 4.2 标记说明

在文档中应该明确说明为什么需要或不需要确认：

**需要确认的接口**：
```markdown
REQUIRES_CONFIRMATION: true

## 安全警告

⚠️ 本接口会对系统数据进行变更，需要用户确认。

变更内容：
- 创建新的数据集成任务
- 任务创建后将开始数据同步

请确保：
- 参数配置正确
- 已获得用户授权
```

**不需要确认的接口**：
```markdown
REQUIRES_CONFIRMATION: false

## 说明

本接口为查询操作，不会修改系统数据，无需用户确认。

注意：虽然使用POST方法，但这是因为查询参数较多，
不适合使用GET方法的URL参数传递。
```

---

### 5. 工作流程

#### 5.1 正常流程

```
1. 用户: "创建集成任务"
   ↓
2. Agent读取Skill文档
   ↓
3. Agent读取接口文档（包含REQUIRES_CONFIRMATION: true）
   ↓
4. Agent准备调用: platform_service(
       doc_path="skills/platform-skill/integration-service/create-task.md",
       ...
     )
   ↓
5. DeepAgents调用_should_interrupt_platform_service:
   - 读取doc_path指向的文档
   - 找到REQUIRES_CONFIRMATION: true
   - 返回True（需要中断）
   ↓
6. DeepAgents中断，返回待确认状态
   ↓
7. 前端展示确认对话框
   ↓
8. 用户确认
   ↓
9. 继续执行
```

#### 5.2 POST查询接口（不需要确认）

```
1. 用户: "批量查询这些表的结构"
   ↓
2. Agent准备调用: platform_service(
       method="POST",  # 虽然是POST
       doc_path="skills/platform-skill/metadata-service/batch-query-schema.md",
       ...
     )
   ↓
3. DeepAgents调用_should_interrupt_platform_service:
   - 读取doc_path指向的文档
   - 找到REQUIRES_CONFIRMATION: false
   - 返回False（不需要中断）
   ↓
4. 直接执行，不中断
   ↓
5. 返回查询结果
```

---

### 6. 优势总结

#### 6.1 与V4方案对比

| 维度 | V4(基于HTTP方法) | V5(基于文档标记) |
|------|-----------------|-----------------|
| 判断依据 | HTTP方法 | 文档中的明确标记 |
| 准确性 | 低（POST查询会误判） | 高（明确标记） |
| 灵活性 | 低（硬编码规则） | 高（文档控制） |
| 可维护性 | 低（需要修改代码） | 高（只需修改文档） |
| 向后兼容 | 差 | 好（默认不确认） |

#### 6.2 核心优势

1. **准确判断**：基于文档明确标记，不会误判POST查询接口
2. **灵活配置**：通过文档控制，无需修改代码
3. **易于维护**：新增接口只需在文档中添加标记
4. **向后兼容**：旧文档没有标记时默认不确认
5. **文档驱动**：符合"给地图不给说明书"的理念

---

### 7. 实施步骤

#### 阶段1：实现中断判断函数（高优先级）

1. 实现`_should_interrupt_platform_service`函数
2. 实现`_resolve_doc_path`函数
3. 配置`interrupt_on`

#### 阶段2：更新接口文档（高优先级）

1. 为所有增删改接口添加`REQUIRES_CONFIRMATION: true`
2. 为所有查询接口添加`REQUIRES_CONFIRMATION: false`
3. 添加安全说明

#### 阶段3：前端中断处理（高优先级）

1. 检测中断状态
2. 展示确认对话框
3. 实现resume/cancel接口

#### 阶段4：测试验证（高优先级）

1. 测试需要确认的接口
2. 测试不需要确认的接口（包括POST查询）
3. 测试文档缺失标记的情况

---

### 8. 文档模板

#### 8.1 需要确认的接口模板

```markdown
# <接口名称>

DOC_GUARD: <uuid>
REQUIRES_CONFIRMATION: true

## 安全警告

⚠️ 本接口会对系统数据进行变更，需要用户确认。

变更内容：
- <具体变更内容1>
- <具体变更内容2>

请确保：
- <前置条件1>
- <前置条件2>

## 接口信息

- **方法**: POST/PUT/DELETE
- **端点**: <endpoint>
- **说明**: <接口说明>

## 请求参数

...
```

#### 8.2 不需要确认的接口模板

```markdown
# <接口名称>

DOC_GUARD: <uuid>
REQUIRES_CONFIRMATION: false

## 说明

本接口为查询操作，不会修改系统数据，无需用户确认。

<如果是POST方法，说明原因>

## 接口信息

- **方法**: GET/POST
- **端点**: <endpoint>
- **说明**: <接口说明>

## 请求参数

...
```

---

### 9. 安全保障

#### 9.1 多层防护

| 层级 | 机制 | 作用 |
|------|------|------|
| **文档层** | REQUIRES_CONFIRMATION标记 | 明确标记是否需要确认 |
| **框架层** | interrupt_on机制 | 自动中断需要确认的操作 |
| **前端层** | 确认对话框 | 用户审核参数 |
| **审计层** | 操作日志 | 事后追溯 |

#### 9.2 防御效果

| 场景 | 防御机制 | 结果 |
|------|---------|------|
| **增删改操作** | 文档标记 + 中断 | ✅ 需要确认 |
| **POST查询** | 文档标记false | ✅ 不需要确认 |
| **参数篡改** | 中断时用户可见 | ✅ 用户发现 |
| **文档缺失标记** | 默认不确认（向后兼容） | ⚠️ 需要补充文档 |

---

### 10. 错误处理

#### 10.1 文档读取失败

```python
try:
    content = resolved_path.read_text(encoding="utf-8")
except Exception as e:
    # 为了安全起见，默认需要确认
    logger.warning(f"读取接口文档失败: {doc_path}, 错误: {e}")
    return True  # 安全优先
```

#### 10.2 文档缺失标记

```python
match = re.search(r'REQUIRES_CONFIRMATION:\s*(true|false)', content)

if match:
    return match.group(1).lower() == 'true'
else:
    # 没有找到标记，默认不需要确认（向后兼容）
    return False
```

---

## 总结

V5方案通过在接口文档中明确标记`REQUIRES_CONFIRMATION`，实现了精确的中断判断：

1. **准确性高**：不会误判POST查询接口
2. **灵活配置**：通过文档控制，无需修改代码
3. **易于维护**：新增接口只需在文档中添加标记
4. **向后兼容**：旧文档默认不确认
5. **文档驱动**：符合Harness理念

这是最准确、最灵活、最易维护的方案！🎉
