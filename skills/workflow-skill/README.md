# Workflow Skill - 工作流创建指南

## 功能描述

本Skill提供创建LangGraph工作流的完整指南和规范，帮助智能体根据业务逻辑编写包含工作流的Skill。

## 使用场景

当需要创建新的业务工作流时，智能体应该参考本Skill中的规范和示例：

1. **固化业务流程**: 将重复性的业务流程固化为工作流
2. **降低token消耗**: 避免每次都需要智能体规划和调用接口(降低96%的token消耗)
3. **提高稳定性**: 通过配置驱动的方式确保执行的一致性
4. **支持复杂逻辑**: 支持条件分支、人工审批等高级特性

## 核心文档

### [create-workflow-skill.md](./create-workflow-skill.md)

完整的工作流创建指南，包含：

- **工作流架构**: 配置驱动、脚本纯逻辑、工具解耦
- **workflow.json规范**: 参数、输出、节点、边的完整定义
- **节点类型**: script(纯逻辑)、tool(工具调用)、human(人工审批)
- **边类型**: normal(普通连接)、conditional(条件分支)
- **脚本规范**: stdin/stdout、纯逻辑、错误处理
- **完整示例**: field-mapping工作流的完整配置
- **最佳实践**: 推荐和不推荐的做法对比
- **常见问题**: Q&A形式的问题解答

## 工作流架构

```
workflow.json (配置)
    ↓
LangGraph (执行引擎)
    ↓
├─ 纯逻辑脚本 (数据处理、验证)
└─ 工具调用 (IT系统交互)
```

## 核心原则

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

## 快速开始

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

### 4. 编写配置

创建workflow.json，定义：
- parameters: 输入参数
- outputs: 输出结果
- nodes: 节点列表
- edges: 边列表
- entry_point: 入口节点

### 5. 编写脚本

遵循脚本规范：
- stdin读取JSON输入
- stdout输出JSON结果
- 只包含纯逻辑
- 完善错误处理

### 6. 编写文档

创建README.md，说明：
- 功能描述
- 使用场景
- 参数说明
- 输出说明
- 工作流程
- 注意事项

### 7. 测试验证

- 重启服务加载工作流
- 使用智能体测试
- 验证各个分支
- 验证错误处理

## 示例参考

参考现有的field-mapping工作流：

- 配置文件: `skills/scenario-skill/field-mapping/workflow.json`
- 脚本目录: `skills/scenario-skill/field-mapping/scripts/`
- 文档: `skills/scenario-skill/field-mapping/README.md`

## 注意事项

1. **脚本必须纯逻辑**: 不允许在脚本中调用外部系统，必须使用tool节点
2. **DOC_GUARD必需**: tool节点调用platform_service时必须提供doc_path或doc_excerpt
3. **参数替换**: tool节点的参数可以使用`{param_name}`引用状态中的值
4. **条件分支**: 同一节点的多个条件边会按顺序匹配，返回第一个匹配的目标
5. **错误处理**: 脚本必须有完善的错误处理，失败时输出`{"success": false, "error": "..."}`
6. **进度消息**: 每个节点应该定义progress消息，用于前端显示

## 相关文档

- [Harness规范](../../docs/harness规范.md)
- [Agent Skills技术文档](../../docs/AgentSkills技术文档.md)
- [Platform Service工具文档](../platform-skill/README.md)
- [场景Skill使用指南](../scenario-skill/README.md)

## 总结

本Skill提供了创建工作流的完整指南，智能体应该：

1. 参考[create-workflow-skill.md](./create-workflow-skill.md)了解完整规范
2. 参考field-mapping示例了解实际应用
3. 遵循核心原则：配置驱动、脚本纯逻辑、工具解耦
4. 编写完善的文档让其他智能体能够理解和使用

通过遵循这些规范，可以创建稳定、高效、易维护的工作流Skill！
