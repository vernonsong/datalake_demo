# 2026-03-23-23-37-fix-thinking-timeline.md

## 问题
前端“思考过程”展示仍存在两类问题：
1) 思考过程中的文本在待办项下展示后，最终回复气泡又重复拼接了同样文本。
2) 思考过程中文本与工具调用实际交错发生，但前端展示为“文本一坨、工具一坨”。

## 修复目标
- 当出现 todos 流程时，思考阶段的 token 文本只进入待办项下的思考时间线，不再进入最终回复气泡。
- 在思考面板内以时间线方式交错展示 text/tool/file，保持事件顺序。

## 变更内容
- `frontend/src/components/Chat.jsx`
  - 引入 `todoTimeline`：按事件到达顺序记录 `{text|tool|file}`。
  - token/tool/file 归属到当前 in_progress 待办；若 todos 已开始但暂无 active（如全部 completed 但尚未 done），回落到最后一个待办，避免误归到最终回复。
  - 当 todos 已开始时，禁止将 token/message 写入最终回复气泡（避免重复）。
- `app/agents/chat_agent.py`
  - 移除流结束时补发的聚合 `message` 事件，避免与思考区 token 重复。

## 验证
- `frontend`: `npm run lint` 通过。

