import os

from langchain_core.tools import tool

from poc.langchain_nonopenai.chat_model import ProviderCompatibleChatModel


def dynamic_token_provider() -> str:
    token = os.getenv("PROVIDER_DYNAMIC_TOKEN")
    if not token:
        raise ValueError("PROVIDER_DYNAMIC_TOKEN is required")
    return token


@tool
def add(a: int, b: int) -> int:
    return a + b


if __name__ == "__main__":
    model = ProviderCompatibleChatModel(
        base_url=os.environ["PROVIDER_CHAT_URL"],
        model=os.environ["PROVIDER_MODEL"],
        token_provider=dynamic_token_provider,
        timeout_seconds=float(os.environ["PROVIDER_TIMEOUT_SECONDS"]),
    )
    runnable = model.bind_tools([add])
    
    print("=== 同步请求示例 ===")
    first = runnable.invoke("请调用 add 工具计算 1+2，只返回结果")
    print(first)
    
    print("\n=== 流式请求示例 ===")
    for chunk in runnable.stream("请用中文介绍一下Python语言的特点"):
        print(chunk.content, end="", flush=True)
    print("\n")
    
    print("\n=== 流式请求 + 工具调用示例 ===")
    for chunk in runnable.stream("请调用 add 工具计算 5+7"):
        if chunk.content:
            print(chunk.content, end="", flush=True)
        if hasattr(chunk, 'tool_call_chunks') and chunk.tool_call_chunks:
            print(f"\n[工具调用]: {chunk.tool_call_chunks}")
    print("\n")
