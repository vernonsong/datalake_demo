# LangChain 非 OpenAI 协议兼容 POC

这个 POC 演示了：

- 服务商不是 OpenAI 协议
- Function Call 的 tool 结构与 OpenAI 一致
- 但请求体要求把 tools 放在 `extrabody.tools`
- 鉴权 token 需要每次动态获取
- 支持同步和流式请求
- 流式响应格式与 OpenAI 标准格式不同
- 仍然以 `BaseChatModel` 方式接入 LangChain

## 文件说明

- `chat_model.py`: `ProviderCompatibleChatModel`，继承 `BaseChatModel`
- `demo.py`: 最小可运行示例

## 接口约定

### 同步请求

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

### 流式请求

请求示意（添加 `"stream": true`）：

```json
{
  "model": "your-model",
  "messages": [{"role": "user", "content": "你好"}],
  "stream": true,
  "extrabody": {
    "tools": [...]
  }
}
```

流式响应示意（SSE 格式，每行以 `data: ` 开头）：

```
data: {"choices":[{"delta":{"role":"assistant","content":"你"}}]}
data: {"choices":[{"delta":{"content":"好"}}]}
data: {"choices":[{"delta":{"content":"！"}}]}
data: [DONE]
```

流式工具调用响应示意：

```
data: {"choices":[{"delta":{"role":"assistant","content":""}}]}
data: {"choices":[{"delta":{"tool_calls":[{"index":0,"id":"call_1","type":"function","function":{"name":"add","arguments":""}}]}}]}
data: {"choices":[{"delta":{"tool_calls":[{"index":0,"function":{"arguments":"{\"a\":"}}]}}]}
data: {"choices":[{"delta":{"tool_calls":[{"index":0,"function":{"arguments":"1,\"b\":2}"}}]}}]}
data: [DONE]
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

## 使用示例

### 同步调用

```python
model = ProviderCompatibleChatModel(
    base_url=os.environ["PROVIDER_CHAT_URL"],
    model=os.environ["PROVIDER_MODEL"],
    token_provider=dynamic_token_provider,
    timeout_seconds=float(os.environ["PROVIDER_TIMEOUT_SECONDS"]),
)
runnable = model.bind_tools([add])
result = runnable.invoke("请调用 add 工具计算 1+2")
print(result)
```

### 流式调用

```python
for chunk in runnable.stream("请用中文介绍一下Python语言的特点"):
    print(chunk.content, end="", flush=True)
```

### 流式调用 + 工具调用

```python
for chunk in runnable.stream("请调用 add 工具计算 5+7"):
    if chunk.content:
        print(chunk.content, end="", flush=True)
    if hasattr(chunk, 'tool_call_chunks') and chunk.tool_call_chunks:
        print(f"\n[工具调用]: {chunk.tool_call_chunks}")
```
