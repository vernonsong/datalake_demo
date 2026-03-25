# LangChain 非 OpenAI 协议兼容 POC

这个 POC 演示了：

- 服务商不是 OpenAI 协议
- Function Call 的 tool 结构与 OpenAI 一致
- 但请求体要求把 tools 放在 `extrabody.tools`
- 鉴权 token 需要每次动态获取
- 仍然以 `BaseChatModel` 方式接入 LangChain

## 文件说明

- `chat_model.py`: `ProviderCompatibleChatModel`，继承 `BaseChatModel`
- `demo.py`: 最小可运行示例

## 接口约定

请求示意：

```json
{
  "model": "your-model",
  "messages": [{"role": "user", "content": "你好"}],
  "extrabody": {
    "tools": [
      {
        "type": "function",
        "function": {
          "name": "add",
          "description": "加法",
          "parameters": {
            "type": "object",
            "properties": {
              "a": {"type": "integer"},
              "b": {"type": "integer"}
            },
            "required": ["a", "b"]
          }
        }
      }
    ]
  }
}
```

响应示意：

```json
{
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "",
        "tool_calls": [
          {
            "id": "call_1",
            "type": "function",
            "function": {"name": "add", "arguments": "{\"a\":1,\"b\":2}"}
          }
        ]
      }
    }
  ]
}
```

## 运行方式

```bash
export PROVIDER_CHAT_URL="https://your-provider/chat/completions"
export PROVIDER_MODEL="your-model"
export PROVIDER_TIMEOUT_SECONDS="30"
export PROVIDER_DYNAMIC_TOKEN="dynamic-token"
python -m poc.langchain_nonopenai.demo
```

`dynamic_token_provider` 可以替换为任意动态逻辑，例如配置中心拉取、STS 刷新或内部签名服务。
