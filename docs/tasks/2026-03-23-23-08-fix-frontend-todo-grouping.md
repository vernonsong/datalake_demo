# 2026-03-23-23-08-fix-frontend-todo-grouping.md

## 问题
前端展示“思考过程”时存在两个反模式：
1) 多个待办项并行/串行执行时，工具调用记录被错误挂在最后一个待办项下。
2) 待办执行中的模型输出文本被渲染到最终对话气泡，而不是对应待办项的“思考过程”里。

## 修复目标
- 工具调用/文件读取按“当前 in_progress 待办”归属展示。
- token 流文本优先展示在当前待办项下，最终对话框展示完整消息（message 事件）。

## 变更内容
- 前端：根据 todo 列表状态计算 active todo index，将 tool_call/file_read/token 归属到该待办；并在待办项下渲染 `todoProcessText`。
- 后端：流式输出结束前补发一次 `message` 事件（聚合 token），让前端可以把最终输出放在对话气泡中。

## 验证
- `frontend`: `npm run lint` 通过。
- 后端/集成：`PYTHONPATH=. python3 scripts/task_completion_validator.py` 通过。

