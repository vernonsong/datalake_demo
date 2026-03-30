import os

from deepagents import create_deep_agent
from deepagents.backends import LocalShellBackend
from langchain_core.tools import tool

from app.core.system_prompt import SYSTEM_PROMPT
from poc.langchain_nonopenai.chat_model import ProviderCompatibleChatModel
from tests.poc_task_tool_direct import PROJECT_ROOT


def dynamic_token_provider() -> str:
    token = os.getenv("PROVIDER_DYNAMIC_TOKEN")
    if not token:
        raise ValueError("PROVIDER_DYNAMIC_TOKEN is required")
    return token




import httpx
from langchain_openai import ChatOpenAI

class DynamicHeaderClient(httpx.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _get_dynamic_token(self):
        # 此处编写获取动态token的逻辑
        return "your-dynamic-token-here"

    def send(self, request: httpx.Request, **kwargs):
        # 动态更新 Authorization 头
        request.headers["Authorization"] = f"Bearer {self._get_dynamic_token()}"
        return super().send(request, **kwargs)

# 初始化带有自定义客户端的模型
llm = ChatOpenAI(
    model="qwen3.5-plus",
    temperature=0.01,
    base_url="https://coding.dashscope.aliyuncs.com/v1",
    api_key="sk-sp-0aa99843838b46729778fac5b6ff5e30",
    http_client=DynamicHeaderClient()
)


agent = create_deep_agent(
    model=llm,
    system_prompt=SYSTEM_PROMPT,
    backend=LocalShellBackend(root_dir=str(PROJECT_ROOT)),
    skills=[

    ]
)
print(agent.invoke({
        "messages": [
            {
                "role": "user",
                "content": "What is langgraph?",
            }
        ]
    }))

