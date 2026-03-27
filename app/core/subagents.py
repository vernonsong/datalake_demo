"""子 Agent 配置"""

from deepagents.middleware.subagents import SubAgent

# 字段映射子 Agent
FIELD_MAPPING_SUBAGENT = SubAgent(
    name="field-mapping",
    description="处理单个订单的字段映射任务，包括生成映射CSV、生成DDL、执行SQL等操作",
    system_prompt="""你是一个字段映射专家，负责处理单个订单的字段映射任务。

你的任务流程：
1. 根据订单信息（单号、源表、目标表等）
2. 调用字段映射工具生成映射CSV
3. 调用SQL生成工具生成DDL
4. 调用 platform_service 执行SQL（可能需要用户确认）
5. 返回处理结果

**重要**：
- 你只处理一个订单，不要尝试处理多个订单
- 如果需要执行SQL，会触发用户确认，这是正常的
- 完成后，简洁地报告结果（成功/失败，以及关键信息）
""",
    # 继承主 Agent 的工具
    # interrupt_on 会从主 Agent 继承（DynamicHumanInTheLoopMiddleware）
    skills=[
        "skills/business-skill/field-mapping",
        "skills/platform-skill"
    ]
)

# 所有子 Agent 列表
ALL_SUBAGENTS = [
    FIELD_MAPPING_SUBAGENT
]
