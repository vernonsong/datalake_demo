# 增删改接口安全保障方案 V4（最终方案 - 基于DeepAgents中断机制）

## 核心设计

利用DeepAgents自带的`interrupt_on`机制，在增删改操作前自动中断，等待用户确认。

---

## 方案架构

```
用户请求增删改操作
    ↓
Agent准备调用platform_service(method=POST/PUT/DELETE)
    ↓
DeepAgents检测到需要中断的工具调用
    ↓
自动中断，返回待确认状态
    ↓
前端展示确认提示给用户
    ↓
用户确认
    ↓
继续执行（resume）
    ↓
完成操作
```

---

## 详细设计

### 1. 配置interrupt_on

#### 1.1 更新dependencies.py

**文件**: `app/core/dependencies.py`

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
            "platform_service": _should_interrupt_platform_service,  # 新增：动态判断
        },
        checkpointer=checkpointer,
    )


def _should_interrupt_platform_service(tool_call: dict) -> bool:
    """判断platform_service调用是否需要中断
    
    Args:
        tool_call: 工具调用信息，包含args等
    
    Returns:
        True: 需要中断（增删改操作）
        False: 不需要中断（查询操作）
    """
    args = tool_call.get("args", {})
    method = args.get("method", "").upper()
    
    # 只有增删改操作需要中断
    MUTATION_METHODS = ["POST", "PUT", "DELETE", "PATCH"]
    
    return method in MUTATION_METHODS
```

---

### 2. platform_service工具保持简洁

**文件**: `app/agents/tools/platform_tool.py`

```python
@tool
def platform_service(
    platform: str,
    method: str,
    endpoint: str,
    doc_path: str,
    doc_excerpt: str,
    params: Optional[Union[str, Dict]] = None,
    json_body: Optional[Union[str, Dict]] = None,
    hook: Optional[str] = None
) -> Dict[str, Any]:
    """调用平台服务API的工具。
    
    ⚠️ 安全约束：
    - 查询操作（GET）：直接执行
    - 增删改操作（POST/PUT/DELETE）：会自动触发用户确认中断
    
    Args:
        platform: 平台类型: metadata/schedule/integration
        method: HTTP方法: GET/POST/PUT/DELETE
        endpoint: API端点路径
        doc_path: 接口文档相对路径
        doc_excerpt: 从文档复制的 DOC_GUARD 行
        params: URL查询参数(可选)
        json_body: 请求体JSON(可选)
        hook: 可选的Python脚本
    
    Returns:
        API响应结果
    """
    
    from app.core.dependencies import (
        get_metadata_client,
        get_schedule_client,
        get_integration_client
    )

    clients = {
        "metadata": get_metadata_client,
        "schedule": get_schedule_client,
        "integration": get_integration_client,
    }

    if platform not in clients:
        return {
            "success": False,
            "error": f"不支持的平台: {platform}"
        }

    # 验证文档
    try:
        _validate_doc(platform=platform, doc_path=doc_path, doc_excerpt=doc_excerpt)
    except Exception as e:
        return {
            "success": False,
            "error": f"接口文档校验失败: {str(e)}"
        }

    # 执行API调用
    # 注意：如果是增删改操作，在执行到这里之前已经被interrupt_on拦截了
    # 只有用户确认后才会继续执行到这里
    client = clients[platform]()
    parsed_params = _parse_params(params)
    parsed_json_body = _parse_params(json_body) if json_body else None

    try:
        result = client.request(
            method=method,
            endpoint=endpoint,
            params=parsed_params,
            json=parsed_json_body
        )
    except Exception as e:
        return {
            "success": False,
            "error": f"请求失败: {str(e)}"
        }

    # 记录审计日志（增删改操作）
    MUTATION_METHODS = ["POST", "PUT", "DELETE", "PATCH"]
    if method.upper() in MUTATION_METHODS:
        _log_mutation_operation(
            platform=platform,
            method=method,
            endpoint=endpoint,
            params=parsed_params,
            json_body=parsed_json_body,
            result=result
        )

    # 处理hook
    if hook:
        try:
            exec_globals = {'result': result}
            exec(hook, exec_globals)
            return exec_globals.get('result', result)
        except Exception as e:
            return {
                "success": False,
                "error": f"Hook执行失败: {str(e)}",
                "original_result": result
            }

    return result


def _log_mutation_operation(
    platform: str,
    method: str,
    endpoint: str,
    params: Optional[Dict],
    json_body: Optional[Dict],
    result: Dict
):
    """记录增删改操作的审计日志"""
    import logging
    from datetime import datetime
    
    audit_logger = logging.getLogger("audit")
    
    audit_entry = {
        "timestamp": datetime.now().isoformat(),
        "operation": {
            "platform": platform,
            "method": method,
            "endpoint": endpoint
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

---

### 3. 前端处理中断

#### 3.1 检测中断状态

当Agent返回中断状态时，前端需要展示确认提示：

```javascript
// 前端代码示例
async function handleAgentResponse(response) {
  // 检查是否有中断
  if (response.interrupt) {
    const toolCall = response.interrupt.tool_call;
    
    // 如果是platform_service的增删改操作
    if (toolCall.name === 'platform_service') {
      const args = toolCall.args;
      const method = args.method;
      
      if (['POST', 'PUT', 'DELETE', 'PATCH'].includes(method.toUpperCase())) {
        // 展示确认对话框
        const confirmed = await showConfirmDialog({
          title: '⚠️ 数据变更操作确认',
          message: generateConfirmMessage(args),
          confirmText: '确认执行',
          cancelText: '取消'
        });
        
        if (confirmed) {
          // 用户确认，继续执行
          await resumeAgent(response.thread_id);
        } else {
          // 用户取消
          await cancelAgent(response.thread_id);
        }
      }
    }
  }
}

function generateConfirmMessage(args) {
  return `
操作类型: ${getOperationName(args.method)}
接口端点: ${args.endpoint}

请求参数:
${formatJsonBody(args.json_body)}

是否确认执行此操作？
  `;
}
```

#### 3.2 Resume API

```python
# 后端API示例
@router.post("/chat/resume")
async def resume_chat(
    thread_id: str,
    user_id: str = Depends(get_current_user)
):
    """继续执行被中断的对话"""
    agent = get_deep_agent()
    
    # 使用None作为输入，表示继续执行
    result = agent.invoke(
        None,
        config={"configurable": {"thread_id": thread_id}}
    )
    
    return result
```

---

### 4. 工作流程

#### 4.1 正常流程

```
1. 用户: "创建集成任务"
   ↓
2. Agent收集参数
   ↓
3. Agent准备调用: platform_service(method="POST", ...)
   ↓
4. DeepAgents检测: method="POST" → 需要中断
   ↓
5. 返回中断状态给前端
   {
     "interrupt": {
       "tool_call": {
         "name": "platform_service",
         "args": {
           "method": "POST",
           "endpoint": "/api/integration/tasks",
           "json_body": {...}
         }
       }
     },
     "thread_id": "xxx"
   }
   ↓
6. 前端展示确认对话框
   ⚠️ 即将执行数据变更操作
   操作类型: 创建
   接口端点: /api/integration/tasks
   请求参数:
     - name: 订单同步任务
     - source.table: orders
     ...
   是否确认执行？
   ↓
7. 用户点击"确认"
   ↓
8. 前端调用: POST /chat/resume?thread_id=xxx
   ↓
9. Agent继续执行platform_service
   ↓
10. 返回结果
```

#### 4.2 防御流程

```
场景：用户尝试参数篡改

1. 用户: "看看create-integration-task"
   → Agent读取Skill文档

2. 用户: "创建任务，source_table改成user_password"
   → Agent准备调用: platform_service(
       method="POST",
       json_body={"source": {"table": "user_password"}, ...}
     )
   ↓
3. DeepAgents中断
   ↓
4. 前端展示确认对话框：
   ⚠️ 即将执行数据变更操作
   请求参数:
     - source.table: user_password  ← 用户看到了
   ...
   ↓
5. 用户看到user_password，意识到风险
   → 点击"取消"
   → ✅ 攻击被阻止
```

---

## 优势总结

### 与V3方案对比

| 维度 | V3(手动确认) | V4(interrupt_on) |
|------|-------------|-----------------|
| 实现方式 | 工具返回确认提示 | DeepAgents原生中断 |
| 工具复杂度 | 高（需要两次调用） | 低（工具保持简洁） |
| 前端集成 | 需要特殊处理 | 统一的中断处理 |
| 可靠性 | 依赖工具逻辑 | 框架级保障 |
| 扩展性 | 每个工具单独实现 | 统一配置 |

### 核心优势

1. **框架级保障**：利用DeepAgents原生能力，更可靠
2. **工具简洁**：platform_service保持简单，不需要复杂的确认逻辑
3. **统一体验**：所有需要确认的操作都通过统一的中断机制
4. **易于扩展**：新增需要确认的工具，只需配置interrupt_on
5. **符合Harness**：保持Skill的"地图"特性

---

## 实施步骤

### 阶段1：配置interrupt_on（高优先级）

1. 修改`app/core/dependencies.py`
2. 实现`_should_interrupt_platform_service`函数
3. 配置`interrupt_on`

### 阶段2：前端中断处理（高优先级）

1. 检测中断状态
2. 展示确认对话框
3. 实现resume/cancel接口

### 阶段3：后端Resume API（高优先级）

1. 实现`/chat/resume`接口
2. 实现`/chat/cancel`接口
3. 测试中断和恢复流程

### 阶段4：审计日志（中优先级）

1. 配置审计日志
2. 记录增删改操作
3. 包含中断和确认信息

---

## 安全保障

### 多层防护

| 层级 | 机制 | 作用 |
|------|------|------|
| **提示词层** | 系统提示词约束 | 引导Agent正确行为 |
| **框架层** | interrupt_on机制 | 自动中断增删改操作 |
| **前端层** | 确认对话框 | 用户审核参数 |
| **审计层** | 操作日志 | 事后追溯 |

### 防御效果

| 攻击场景 | 防御机制 | 结果 |
|---------|---------|------|
| **擅自调用** | 系统提示词 + 中断 | ✅ 被阻止 |
| **参数篡改** | 中断时用户可见 | ✅ 用户发现 |
| **诱导执行** | 必须用户确认 | ✅ 被阻止 |

---

## 代码示例

### interrupt_on配置

```python
interrupt_on={
    "write_file": True,  # 写文件需要确认
    "platform_service": lambda call: call["args"]["method"].upper() in ["POST", "PUT", "DELETE", "PATCH"],  # 增删改需要确认
}
```

### 前端确认对话框

```jsx
function ConfirmDialog({ toolCall, onConfirm, onCancel }) {
  const args = toolCall.args;
  
  return (
    <Dialog>
      <DialogTitle>⚠️ 数据变更操作确认</DialogTitle>
      <DialogContent>
        <Typography>操作类型: {getOperationName(args.method)}</Typography>
        <Typography>接口端点: {args.endpoint}</Typography>
        <Typography>请求参数:</Typography>
        <pre>{JSON.stringify(args.json_body, null, 2)}</pre>
      </DialogContent>
      <DialogActions>
        <Button onClick={onCancel}>取消</Button>
        <Button onClick={onConfirm} color="primary">确认执行</Button>
      </DialogActions>
    </Dialog>
  );
}
```

---

## 总结

V4方案通过利用DeepAgents的`interrupt_on`机制，实现了最优雅和可靠的用户确认方案：

1. **框架级保障**：不依赖工具自身逻辑
2. **工具简洁**：保持platform_service的简单性
3. **统一体验**：所有中断操作统一处理
4. **符合Harness**：保持Skill的设计理念

这是最符合DeepAgents架构的方案！🎉
