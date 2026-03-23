# Agent Skills 技术文档

## 一、背景与问题

### 1.1 MCP的局限性

MCP（Model Context Protocol）由Anthropic提出，核心价值是**标准化智能体与外部工具/资源的通信方式**。但在实际应用中存在两个根本性问题：

| 问题 | 描述 | 影响 |
|------|------|------|
| **上下文爆炸** | MCP服务器通常暴露数十上百个工具，其完整JSON Schema会占用数万个token | 成本飙升、推理能力下降 |
| **能力鸿沟** | 拥有连接能力 ≠ 知道如何使用 | 智能体缺乏领域知识 |

### 1.2 Agent Skills的诞生

Agent Skills是Anthropic在2025年初提出的概念，核心解决：**"连接性"与"能力"应该分离**

- **MCP** = 提供"手"（标准化访问接口）
- **Skills** = 提供"操作手册"（领域知识+SOP）

---

## 二、核心设计理念

### 2.1 职责分离

```
┌─────────────────────────────────────────────────────────┐
│                    应用层 (Agent Skills)                │
│         领域知识、工作流、最佳实践、触发时机              │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│                    传输层 (MCP)                          │
│         标准化接口、工具调用、资源访问                    │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│                    基础设施层                           │
│            数据库、API、文件系统、外部服务               │
└─────────────────────────────────────────────────────────┘
```

### 2.2 渐进式披露（Progressive Disclosure）

Skills的核心创新是将信息分为**三层**，智能体按需加载：

| 层级 | 加载时机 | 内容 | Token消耗 |
|------|----------|------|----------|
| **第一层：元数据** | Agent启动时 | 扫描所有Skill，读取Frontmatter | ~100 token/技能 |
| **第二层：指令主体** | 判断任务高度相关时 | 完整SKILL.md，包含工作流、示例 | 1k-5k token |
| **第三层：附加资源** | 需要时 | 脚本、配置文件、参考文档 | 按需加载 |

---

## 三、Skill结构规范

### 3.1 目录结构

```
skills/
├── skill-name/
│   ├── SKILL.md           # 必需：主技能文件
│   ├── parse_script.py    # 可选：执行脚本
│   ├── forms.md          # 可选：详细指南
│   └── templates/        # 可选：模板文件
│       ├── template1.pdf
│       └── template2.json
```

### 3.2 SKILL.md 格式规范

```yaml
---
# === 必需字段 ===
name: skill-name           # 唯一标识符，kebab-case命名
description: >
  简洁精确的描述，说明：
  1. 这个技能做什么
  2. 什么时候应该使用
  3. 它的核心价值是什么
  # 注意：description是Agent选择技能的唯一依据！

# === 可选字段 ===
version: 1.0.0             # 语义化版本
allowed_tools: [tool1]     # 可调用工具白名单
required_context: [ctx1]  # 需要的上下文
tags: [database, analysis] # 分类标签
author: YourName<email>    # 作者信息
---

# 技能标题

## 概述
（详细介绍、使用场景、技术背景）

## 前置条件
（环境配置、依赖项等）

## 工作流程
（详细步骤，告诉智能体如何执行）

## 最佳实践
（经验总结、注意事项、常见陷阱）

## 示例
（具体案例，帮助理解）

## 故障排查
（常见问题与解决方案）
```

---

## 四、编写高质量Skills的原则

### 4.1 精准的Description

```yaml
# ❌ 不好的description
description: 处理数据库查询

# ✅ 好的description
description: >
  将中文业务问题转换为SQL查询并分析MySQL employees示例数据库。
  适用于员工信息查询、薪资统计、部门分析、职位变动历史等场景。
  当用户询问关于员工、薪资、部门的数据时使用此技能。
```

### 4.2 单一职责原则

```
# ❌ 一个技能做太多事
skill: "通用数据分析"

# ✅ 职责分明
skill: "mysql-employees-analysis"    # 专门分析employees数据库
skill: "sales-data-analysis"         # 专门分析销售数据
skill: "user-behavior-analysis"      # 专门分析用户行为
```

### 4.3 确定性优先原则

```yaml
# ❌ 依赖LLM生成可能出错
生成Excel文件内容返回给用户

# ✅ 使用脚本处理复杂任务
# 在SKILL.md中指导Agent调用export_excel.py脚本
```

---

## 五、Skills + MCP 混合架构

### 5.1 典型工作流

```
用户：分析公司内部谁的话语权最高

1. Skills层  → 识别数据分析任务，加载mysql-analysis技能
2. Skills层  → 分解子步骤：查询管理关系、薪资对比、任职时长
3. MCP层    → 执行具体SQL查询，返回结果
4. Skills层  → 解读数据，生成综合分析
5. 返回结果给用户
```

### 5.2 架构优势

| 优势 | 说明 |
|------|------|
| 关注点分离 | MCP专注"能力"，Skills专注"智慧" |
| 成本优化 | 渐进式加载降低90%以上token消耗 |
| 可维护性 | 业务逻辑与基础设施解耦 |
| 复用性 | 同一MCP可被多个Skills使用 |

---

## 六、与本项目的结合

### 6.1 项目Skill目录设计

```
skills/
├── business/          # 业务Skill：数据管理部规范
│   ├── data-quality-check/
│   ├── schedule-standard/
│   └── lake-table-spec/
├── platform/          # 平台Skill：上游接口调用
│   ├── metadata-api/      # 元数据API
│   ├── schedule-api/      # 调度API
│   ├── integration-api/   # 集成API
│   └── lineage-api/       # 血缘API
├── scene/             # 场景Skill：已支持的场景
│   ├── add-lake-table/
│   ├── modify-schedule/
│   └── add-field/
└── temp/              # 临时Skill：编排产出待验证
    └── user-defined-xxx/
```

### 6.2 三个智能体的Skill权限

| 智能体 | 可用Skills | 说明 |
|--------|-----------|------|
| 对话智能体 | business, scene | 意图识别，业务引导 |
| 编排智能体 | platform, business | 选取skill，编排工作流 |
| 验证智能体 | platform, business, temp | 验证工作流正确性 |

---

## 七、参考资料

- [Anthropic Agent Skills 官方文档](https://docs.anthropic.com/en/docs/agent-skills)
- [Anthropic Skills GitHub仓库](https://github.com/anthropics/skills)
- [Model Context Protocol规范](https://modelcontextprotocol.io/)
