# 任务记录：LangChain 非 OpenAI 协议 BaseChatModel POC

## 任务目标

在不修改现有后端服务代码的前提下，提供一个独立 POC：当模型服务商接口不完全遵循 OpenAI 协议（`tools` 位于 `extrabody.tools`，并使用动态 token 鉴权）时，仍可通过 LangChain `BaseChatModel` 兼容 function call。

## 实施内容

- 新增 `poc/langchain_nonopenai/chat_model.py`
  - 提供 `ProviderCompatibleChatModel`，继承 `BaseChatModel`
  - 支持动态 token 提供器 `token_provider`
  - 将绑定工具转换后放入 `extrabody.tools`
  - 兼容解析服务商返回的 `tool_calls` 到 LangChain 标准 `AIMessage.tool_calls`
- 新增 `poc/langchain_nonopenai/demo.py`
  - 提供最小可运行用法
- 新增 `poc/langchain_nonopenai/README.md`
  - 说明请求/响应约定与运行方式
- 新增 `tests/unit/test_nonopenai_chat_model_poc.py`
  - 验证 `bind_tools` 会写入 `extrabody.tools`
  - 验证服务商 `tool_calls` 能被转换为 LangChain tool call

## 影响范围

- 仅新增 POC 目录与测试文件
- 未修改 `app/` 后端服务代码

## 验证记录

- 执行单测：
  - `pytest tests/unit/test_nonopenai_chat_model_poc.py`
- 执行任务完成验证器：
  - `python3 scripts/task_completion_validator.py`
