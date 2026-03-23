# 数据入湖平台 - Harness工程规范

## 一、核心原则

### 1.1 人类掌舵，智能体执行

本项目遵循OpenAI Harness工程规范：
- **人类职责**：设计环境、明确意图、构建反馈回路
- **智能体职责**：执行任务、编写代码、自我审核
- **不直接编写代码**：所有代码由智能体生成

### 1.2 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                      人类工程师                             │
│   设计环境 │ 明确意图 │ 构建反馈回路 │ 验证结果              │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                     智能体层                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │  对话智能体  │  │  编排智能体  │  │  验证智能体  │       │
│  │ (意图识别)   │  │ (工作流编排) │  │ (结果验证)   │       │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘       │
│         │                 │                 │              │
│         └─────────────────┼─────────────────┘              │
│                           │                                │
│                    ┌──────▼──────┐                        │
│                    │   Skill层   │                        │
│                    │  (操作手册)  │                        │
│                    └──────┬──────┘                        │
└───────────────────────────┼───────────────────────────────┘
                            │
┌───────────────────────────▼───────────────────────────────┐
│                     基础设施层                            │
│   Mock服务 │ LLM服务 │ 配置中心 │ Skill存储               │
└──────────────────────────────────────────────────────────┘
```

---

## 二、智能体设计

### 2.1 三个智能体

| 智能体 | 职责 | 可用Skills | 角色 |
|--------|------|-----------|------|
| 对话智能体 | 意图识别、业务引导、解答 | business, scene | 用户入口 |
| 编排智能体 | 选取Skill、编排工作流 | platform, business | 工作流生成 |
| 验证智能体 | 验证工作流正确性 | platform, business, temp | 质量把控 |

### 2.2 智能体通信协议

```
用户 → 对话智能体 → 编排智能体 → 验证智能体 → 执行
                      ↑              ↓
                      └──────────────┘
                         (循环验证)
```

---

## 三、Skill机制

### 3.1 Skill目录结构

```
skills/
├── business/          # 业务Skill：数据管理部规范
│   ├── data-quality-check/
│   │   └── SKILL.md
│   ├── schedule-standard/
│   └── lake-table-spec/
├── platform/          # 平台Skill：上游接口调用
│   ├── metadata-api/
│   ├── schedule-api/
│   ├── integration-api/
│   └── lineage-api/
├── scene/             # 场景Skill：已支持的场景
│   ├── add-lake-table/
│   ├── modify-schedule/
│   └── add-field/
└── temp/              # 临时Skill：编排产出待验证
    └── user-defined-xxx/
```

### 3.2 SKILL.md格式（渐进式披露）

```yaml
---
name: skill-name
description: >
  精确描述：做什么、何时用、核心价值
version: 1.0.0
allowed_tools: [tool1, tool2]
tags: [database, analysis]
---

# 技能标题

## 概述
（详细介绍）

## 工作流程
（详细步骤）

## 最佳实践
（经验总结）

## 示例
（帮助理解）
```

---

## 四、反馈回路

### 4.1 验证循环

```
编排智能体 → 生成工作流 → 验证智能体
                              ↓
                         验证通过?
                        ↙         ↘
                       是           否
                        ↓           ↓
                     执行工作流   反馈给编排智能体
                                    ↓
                              重新编排
```

### 4.2 人工干预点

- 场景确认：编排前需用户确认
- 审批节点：关键操作需人工审批
- 最终验证：执行完成后用户确认结果

---

## 五、工程规范

### 5.1 文档结构

```
docs/
├── api/                    # 接口文档
│   └── README.md
├── skills/                 # Skill文档
│   ├── business/
│   ├── platform/
│   └── scene/
├── agents/                 # 智能体配置
│   └── AGENTS.md
├── workflow/               # 工作流定义
└── design/                 # 设计文档
```

### 5.2 AGENTS.md（智能体指南）

每个智能体需要明确的AGENTS.md，包含：
- 角色定义
- 能力边界
- 工作流程
- 约束条件

### 5.3 渐进式披露原则

1. **初始上下文**：仅提供必要的入口信息
2. **按需加载**：根据任务需要加载详细文档
3. **指向更深层次**：始终指向真实信息来源

---

## 六、质量保证

### 6.1 自动验证

- 工作流JSON Schema验证
- Skill格式验证
- 依赖关系验证

### 6.2 持续清理

- 定期扫描过时文档
- 检查 Skill 一致性
- 验证工作流有效性

---

## 七、配置管理

### 7.1 配置中心

所有配置通过配置中心管理：

```json
{
  "llm": {
    "api_base": "https://coding.dashscope.aliyuncs.com/v1",
    "model": "qwen3.5-plus",
    "temperature": 0.7,
    "max_tokens": 2000
  },
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
  }
}
```

### 7.2 环境变量

```
ALI_API_KEY=sk-sp-xxx  # 阿里云API Key
```

---

## 八、参考

- [OpenAI Harness Engineering](https://openai.com/zh-Hans-CN/index/harness-engineering/)
- [Anthropic Agent Skills](https://docs.anthropic.com/en/docs/agent-skills)
- [Model Context Protocol](https://modelcontextprotocol.io/)
