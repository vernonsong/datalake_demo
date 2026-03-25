# 增删改接口安全保障方案 V3（最终方案）

## 方案回顾

### V1方案：SKILL_GUARD
- ❌ 无法防止参数篡改
- ✅ 符合Skill设计理念

### V2方案：Skill封装调用
- ✅ 可以防止参数篡改
- ❌ 违背Skill设计理念（过度封装）

### V3方案：系统提示词 + 用户确认（推荐）
- ✅ 可以防止参数篡改
- ✅ 符合Skill设计理念
- ✅ 用户体验好

---

## V3方案设计

### 核心机制

```
┌─────────────────────────────────────────────┐
│  第1层：系统提示词约束                       │
│  - 明确禁止擅自调用增删改接口               │
│  - 要求必须基于Skill                         │
│  - 要求必须获得用户确认                      │
└──────────────────┬──────────────────────────┘
                   ↓
┌─────────────────────────────────────────────┐
│  第2层：工具层用户确认                       │
│  - 增删改操作自动触发用户确认               │
│  - 展示操作详情和风险提示                   │
│  - 用户明确同意后才执行                      │
└──────────────────┬──────────────────────────┘
                   ↓
┌─────────────────────────────────────────────┐
│  第3层：审计日志                             │
│  - 记录所有增删改操作                        │
│  - 包含用户确认信息                          │
└─────────────────────────────────────────────┘
```

---

## 详细设计

### 1. 系统提示词约束

#### 1.1 更新SYSTEM_PROMPT

**文件**: `app/core/system_prompt.py`

```python
SYSTEM_PROMPT = """
你是一个智能数据平台助手，帮助用户完成数据入湖相关任务。

## 核心原则

1. **Harness工程规范**：人类掌舵，智能体执行
2. **渐进式披露**：给地图不给说明书
3. **Skill驱动**：所有操作必须基于已有的Skill

## 增删改操作安全规范

⚠️ **重要约束**：涉及数据变更的操作（POST/PUT/DELETE）必须严格遵守以下规范：

### 1. 必须基于Skill

- 增删改操作必须有对应的Skill指导
- 不允许擅自调用增删改接口
- 必须先阅读Skill文档，理解业务场景和约束

### 2. 必须获得用户确认

在执行增删改操作前，必须：
1. 向用户清晰说明将要执行的操作
2. 列出关键参数和影响范围
3. 明确告知风险
4. 等待用户明确确认（"确认"、"同意"、"执行"等）

### 3. 确认信息模板

```
⚠️ 即将执行数据变更操作，请确认：

操作类型: [创建/更新/删除]
操作对象: [具体对象，如"集成任务"]
关键参数:
  - 参数1: 值1
  - 参数2: 值2
  ...

影响范围: [说明影响]
风险提示: [说明风险]

是否确认执行？（请回复"确认"以继续）
```

### 4. 禁止行为

❌ 禁止在没有用户明确确认的情况下执行增删改操作
❌ 禁止在用户只是"查看"或"了解"Skill时就执行操作
❌ 禁止根据用户的模糊指令（如"试试看"）执行增删改操作
❌ 禁止擅自修改用户提供的参数

### 5. 示例对话

**正确示例**：
```
用户: 帮我创建一个集成任务
Agent: 好的，我需要一些信息来创建集成任务。请提供：
      - 任务名称
      - 源数据库和表
      - 目标数据库和表
      
用户: 任务名称是"订单同步"，源表是source_db.orders，目标表是dw_target.dw_orders

Agent: ⚠️ 即将执行数据变更操作，请确认：
      
      操作类型: 创建集成任务
      操作对象: 数据集成任务
      关键参数:
        - 任务名称: 订单同步
        - 源表: source_db.orders
        - 目标表: dw_target.dw_orders
      
      影响范围: 将创建一个新的数据集成任务
      风险提示: 任务创建后将开始数据同步
      
      是否确认执行？

用户: 确认

Agent: [执行创建操作]
      ✅ 集成任务创建成功，任务ID: 123
```

**错误示例**：
```
用户: 帮我看看create-integration-task这个Skill
Agent: [读取Skill文档]
      这个Skill用于创建数据集成任务...

用户: 那就创建一个吧，源表改成sensitive_table
Agent: ❌ 错误做法：直接执行
      ✅ 正确做法：
         我注意到您想创建集成任务，但有几个问题需要确认：
         1. 您提到的sensitive_table是敏感表，通常不建议同步
         2. 我需要完整的参数信息（任务名称、目标表等）
         3. 请明确确认是否要创建此任务
```

## 工具使用规范

### platform_service工具

- 查询操作（GET）：可以灵活使用
- 增删改操作（POST/PUT/DELETE）：必须遵守上述安全规范

---

你的职责是帮助用户完成任务，但必须确保操作的安全性和合规性。
"""
```

---

### 2. 工具层用户确认机制

#### 2.1 增强platform_service工具

**文件**: `app/agents/tools/platform_tool.py`

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
平台服务工具 - 支持用户确认
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any, Union
from langchain_core.tools import tool


@tool
def platform_service(
    platform: str,
    method: str,
    endpoint: str,
    doc_path: str,
    doc_excerpt: str,
    params: Optional[Union[str, Dict]] = None,
    json_body: Optional[Union[str, Dict]] = None,
    hook: Optional[str] = None,
    user_confirmed: bool = False  # 新增参数
) -> Dict[str, Any]:
    """调用平台服务API的工具。

    ⚠️ 重要约束：
    - 查询操作（GET）：可以直接调用
    - 增删改操作（POST/PUT/DELETE）：必须先获得用户确认
    
    Args:
        platform: 平台类型: metadata/schedule/integration
        method: HTTP方法: GET/POST/PUT/DELETE
        endpoint: API端点路径
        doc_path: 接口文档相对路径
        doc_excerpt: 从文档复制的 DOC_GUARD 行
        params: URL查询参数(可选)
        json_body: 请求体JSON(可选)
        hook: 可选的Python脚本
        user_confirmed: 用户是否已确认（增删改操作必填）
    
    Returns:
        API响应结果，或需要用户确认的提示
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

    # 检查是否需要用户确认
    MUTATION_METHODS = ["POST", "PUT", "DELETE", "PATCH"]
    
    if method.upper() in MUTATION_METHODS:
        if not user_confirmed:
            # 生成确认提示
            confirmation_prompt = _generate_confirmation_prompt(
                method=method,
                endpoint=endpoint,
                params=params,
                json_body=json_body
            )
            
            return {
                "success": False,
                "requires_confirmation": True,
                "confirmation_prompt": confirmation_prompt,
                "message": "增删改操作需要用户确认。请向用户展示确认提示，获得明确同意后，"
                          "再次调用本工具并设置 user_confirmed=True"
            }

    # 执行API调用
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
    if method.upper() in MUTATION_METHODS:
        _log_mutation_operation(
            platform=platform,
            method=method,
            endpoint=endpoint,
            params=parsed_params,
            json_body=parsed_json_body,
            result=result,
            user_confirmed=user_confirmed
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


def _generate_confirmation_prompt(
    method: str,
    endpoint: str,
    params: Optional[Dict],
    json_body: Optional[Dict]
) -> str:
    """生成用户确认提示"""
    
    operation_names = {
        "POST": "创建",
        "PUT": "更新",
        "PATCH": "更新",
        "DELETE": "删除"
    }
    
    operation = operation_names.get(method.upper(), "变更")
    
    prompt_lines = [
        "⚠️ 即将执行数据变更操作，请确认：",
        "",
        f"操作类型: {operation}",
        f"接口端点: {endpoint}",
    ]
    
    if json_body:
        prompt_lines.append("")
        prompt_lines.append("请求参数:")
        for key, value in json_body.items():
            prompt_lines.append(f"  - {key}: {value}")
    
    if params:
        prompt_lines.append("")
        prompt_lines.append("查询参数:")
        for key, value in params.items():
            prompt_lines.append(f"  - {key}: {value}")
    
    prompt_lines.extend([
        "",
        "影响范围: 将对系统数据进行变更",
        "风险提示: 请确保参数正确，操作不可撤销",
        "",
        "是否确认执行？（请回复"确认"以继续）"
    ])
    
    return "\n".join(prompt_lines)


def _log_mutation_operation(
    platform: str,
    method: str,
    endpoint: str,
    params: Optional[Dict],
    json_body: Optional[Dict],
    result: Dict,
    user_confirmed: bool
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
        },
        "user_confirmed": user_confirmed
    }
    
    audit_logger.info(json.dumps(audit_entry, ensure_ascii=False))


# ... 其他辅助函数保持不变
```

---

### 3. Agent工作流程

#### 3.1 正常流程

```
1. 用户请求创建任务
   ↓
2. Agent识别需要create-integration-task Skill
   ↓
3. Agent读取Skill文档
   ↓
4. Agent收集必要参数
   ↓
5. Agent生成确认提示，展示给用户
   ↓
6. 用户回复"确认"
   ↓
7. Agent调用platform_service(user_confirmed=True)
   ↓
8. 执行API调用 + 记录审计日志
   ↓
9. 返回结果
```

#### 3.2 防御流程

```
场景：用户尝试参数篡改

1. 用户: "看看create-integration-task"
   → Agent读取Skill文档

2. 用户: "创建任务，source_table改成sensitive_table"
   → Agent识别到增删改操作
   → Agent生成确认提示：
   
   ⚠️ 即将执行数据变更操作，请确认：
   
   操作类型: 创建
   接口端点: /api/integration/tasks
   请求参数:
     - name: ...
     - source.table: sensitive_table  ← 用户可以看到
     - target.table: ...
   
   是否确认执行？

3. 用户看到sensitive_table，意识到风险
   → 用户: "等等，不对，应该是orders表"
   → ✅ 攻击被用户自己阻止
```

---

## 安全保障

### 多层防护

| 层级 | 机制 | 作用 |
|------|------|------|
| **提示词层** | 系统提示词约束 | 引导Agent正确行为 |
| **工具层** | 用户确认机制 | 强制用户审核 |
| **审计层** | 操作日志 | 事后追溯 |

### 防御效果

| 攻击场景 | 防御机制 | 结果 |
|---------|---------|------|
| **擅自调用** | 系统提示词 + 用户确认 | ✅ 被阻止 |
| **参数篡改** | 用户确认时可见 | ✅ 用户发现 |
| **诱导执行** | 必须明确确认 | ✅ 被阻止 |

---

## 用户体验

### 正常使用

```
用户: 帮我创建一个订单同步任务

Agent: 好的，我需要一些信息：
      - 源数据库和表？
      - 目标数据库和表？

用户: 源表是source_db.orders，目标表是dw_target.dw_orders

Agent: ⚠️ 即将执行数据变更操作，请确认：
      
      操作类型: 创建集成任务
      请求参数:
        - name: 订单同步任务
        - source.database: source_db
        - source.table: orders
        - target.database: dw_target
        - target.table: dw_orders
      
      是否确认执行？

用户: 确认

Agent: ✅ 集成任务创建成功
```

### 攻击被阻止

```
用户: 看看create-integration-task

Agent: [展示Skill文档内容]

用户: 创建任务，source_table改成user_password

Agent: ⚠️ 即将执行数据变更操作，请确认：
      
      操作类型: 创建集成任务
      请求参数:
        - source.table: user_password  ← 用户看到了
        ...
      
      是否确认执行？

用户: 等等，这不对...（发现问题）
```

---

## 实施步骤

### 阶段1：更新系统提示词（高优先级）

1. 修改`app/core/system_prompt.py`
2. 添加增删改操作安全规范
3. 提供示例对话

### 阶段2：增强platform_service工具（高优先级）

1. 添加`user_confirmed`参数
2. 实现确认提示生成
3. 实现审计日志记录

### 阶段3：测试和验证（高优先级）

1. 测试正常使用场景
2. 测试攻击场景
3. 验证用户体验

### 阶段4：文档更新（中优先级）

1. 更新Skill文档说明
2. 更新API文档
3. 添加安全使用指南

---

## 优势总结

1. **符合Harness规范**：保持Skill的"地图"特性
2. **用户友好**：通过确认机制让用户参与决策
3. **安全可靠**：多层防护，难以绕过
4. **实施简单**：主要是提示词和工具层改动
5. **灵活性高**：不影响Skill的设计和扩展
6. **可审计**：所有操作有日志记录

---

## 与其他方案对比

| 维度 | V1(SKILL_GUARD) | V2(Skill封装) | V3(提示词+确认) |
|------|----------------|--------------|----------------|
| 防止擅自调用 | ✅ | ✅ | ✅ |
| 防止参数篡改 | ❌ | ✅ | ✅ |
| 符合Skill设计 | ✅ | ❌ | ✅ |
| 用户体验 | 一般 | 一般 | ✅ 好 |
| 实施复杂度 | 中 | 高 | 低 |
| 维护成本 | 中 | 高 | 低 |

---

## 总结

V3方案通过**系统提示词约束 + 用户确认机制**，在保持Skill设计理念的同时，提供了可靠的安全保障。用户确认机制不仅能防止攻击，还能让用户参与决策，提升了透明度和信任度。

这是最符合Harness工程理念的方案：**人类掌舵，智能体执行**。
