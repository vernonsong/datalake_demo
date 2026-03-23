# 2026-03-23-00-08-fix-platform-tool-hook-leak.md

## 问题
`platform_service` 工具 docstring 中包含可直接照抄的 hook 示例，且与业务验证场景（例如将 schema 转 CSV）高度同构，导致智能体即使不理解 hook 语义，也可能通过复制示例而在验证中“误通过”。

## 修复目标
- 工具层不再提供任何可直接照抄的 hook 示例。
- hook 的正确用法应由对应 Skill / 平台文档提供，并可通过现有“先读文档再调用”的机制约束。

## 变更内容
- 删除 `platform_service` docstring 中的 hook 基础示例与 CSV 生成示例，仅保留抽象说明。

## 验证方式
- `PYTHONPATH=. pytest -q`
- `PYTHONPATH=. python3 scripts/task_completion_validator.py`

