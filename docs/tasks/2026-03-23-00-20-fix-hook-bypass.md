# 2026-03-23-00-20-fix-hook-bypass.md

## 问题
在字段映射流程中，智能体未使用 `platform_service(hook=...)` 完成 CSV 落盘，而是通过执行 `python3 -c ...` 自行生成 CSV，导致：
- 不符合 Skill 约束（步骤 2 明确要求用 hook）
- 验证用例可能“误通过”（通过复制脚本而非理解 hook）

## 修复目标
- 在 Skill 文档层面明确“必须用 hook，禁止命令替代”。
- 在系统提示中加入强约束，避免模型选择绕过路径。
- 在验证器中增加可检测的反模式判定（python3 -c 写 CSV）。

## 变更内容
- 更新 `skills/business-skill/field-mapping/SKILL.md`：步骤 2 强制使用 `platform_service` 的 `hook` 落盘 CSV，并将 `python3 -c/execute` 生成 CSV 列为反模式。
- 更新 `app/core/system_prompt.py`：增加规则，当 Skill 明确要求 hook 时，禁止通过命令执行替代 hook。
- 更新 `scripts/task_completion_validator.py`：新增“字段映射-CSV必须用hook”用例，并检测 `execute/python3 -c` 生成 CSV 的绕过行为。

## 验证方式
- `PYTHONPATH=. pytest -q`
- `PYTHONPATH=. python3 scripts/task_completion_validator.py`

