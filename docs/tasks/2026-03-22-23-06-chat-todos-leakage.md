# 任务: 修复聊天接口 todos 串线问题

## 任务描述
排查并修复“仅发送问候语却返回上次字段映射 todos”的问题，确保每次会话上下文隔离。

## 完成内容

### 1. 问题定位
- `conversation_id` 缺失时后端固定使用 `default` 作为线程 ID，导致历史状态复用。
- 流式接口会把首个状态快照中的历史 `todos` 直接透传给前端，因此问候语也会先收到上次任务清单。
- 前端首条消息发送时可能不携带 `conversation_id`，进一步放大了该问题。

### 2. 修复实现
- 文件: `app/agents/chat_agent.py`
- 新增线程 ID 解析逻辑：当 `conversation_id` 缺失时按 `user_id + 时间戳 + 随机后缀` 生成唯一线程 ID，避免使用固定 `default`。
- `chat` 响应中的 `conversation_id` 改为返回实际使用的线程 ID。
- `chat_stream` 增加首帧 `todos` 基线捕获逻辑，忽略历史快照，仅在本轮 `todos` 发生变化时推送事件。
- 文件: `frontend/src/components/Chat.jsx`
- 首次发送前在前端生成并设置 `conversationId`，同一次对话后续请求复用该 ID，避免空会话 ID 请求。
- 移除“首轮结束后才生成会话 ID”的逻辑。
- 文件: `tests/unit/test_chat_agent.py`
- 新增用例覆盖：
  - 缺失 `conversation_id` 时生成非 `default` 线程 ID
  - 显式 `conversation_id` 时正确透传
  - 流式问候场景不再输出历史 `todos`

### 3. 回归验证
- 执行: `PYTHONPATH=. pytest tests/unit/test_chat_agent.py`
- 结果: `3 passed`
- 执行: `PYTHONPATH=. pytest tests/unit/test_dependencies.py tests/integration/test_config_service.py`
- 结果: `23 passed`
- 执行: `npx eslint src/components/Chat.jsx`
- 结果: 无报错
- 接口验证:
  - `POST /chat/`（仅“你好”，不带 conversation_id）返回 token + done，不含 todos
  - 同一 `conversation_id` 先执行映射再发送“你好”，映射请求 `todos=3`，问候请求 `todos=0`

## 验证状态
- 已完成核心问题验证
