import json
from typing import Any, Callable, Dict, List, Optional, Sequence

import requests
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.utils.function_calling import convert_to_openai_tool


class ProviderCompatibleChatModel(BaseChatModel):
    base_url: str
    model: str
    token_provider: Callable[[], str]
    timeout_seconds: float

    @property
    def _llm_type(self) -> str:
        return "provider_compatible_chat_model"

    def bind_tools(self, tools: Sequence[Any], **kwargs: Any) -> Any:
        formatted_tools = [convert_to_openai_tool(tool) for tool in tools]
        extra_body = kwargs.pop("extrabody", None)
        if extra_body is None:
            extra_body = {}
        extra_body = dict(extra_body)
        extra_body["tools"] = formatted_tools
        return self.bind(extrabody=extra_body, **kwargs)

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": [self._to_provider_message(m) for m in messages],
        }
        if stop:
            payload["stop"] = stop

        for key in ["temperature", "max_tokens", "top_p", "frequency_penalty", "presence_penalty"]:
            if key in kwargs and kwargs[key] is not None:
                payload[key] = kwargs[key]

        explicit_tools = kwargs.pop("tools", None)
        explicit_extrabody = kwargs.pop("extrabody", None)
        bound_extrabody = kwargs.pop("extra_body", None)
        extra_body = self._merge_extrabody(explicit_extrabody, bound_extrabody)
        if explicit_tools is not None:
            if extra_body is None:
                extra_body = {}
            extra_body["tools"] = explicit_tools
        if extra_body is not None:
            payload["extrabody"] = extra_body

        token = self.token_provider()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        response = requests.post(
            self.base_url,
            headers=headers,
            json=payload,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()

        choice = data["choices"][0]
        message = choice["message"]
        tool_calls = self._to_langchain_tool_calls(message.get("tool_calls"))
        additional_kwargs: Dict[str, Any] = {}
        if message.get("tool_calls"):
            additional_kwargs["tool_calls"] = message["tool_calls"]

        ai_message = AIMessage(
            content=message.get("content") or "",
            additional_kwargs=additional_kwargs,
            tool_calls=tool_calls,
        )
        generation = ChatGeneration(message=ai_message)
        llm_output = {"provider_response": data}
        return ChatResult(generations=[generation], llm_output=llm_output)

    def _to_provider_message(self, message: BaseMessage) -> Dict[str, Any]:
        if isinstance(message, HumanMessage):
            return {"role": "user", "content": message.content}
        if isinstance(message, SystemMessage):
            return {"role": "system", "content": message.content}
        if isinstance(message, ToolMessage):
            payload = {
                "role": "tool",
                "content": message.content,
            }
            if getattr(message, "tool_call_id", None):
                payload["tool_call_id"] = message.tool_call_id
            return payload
        if isinstance(message, AIMessage):
            payload = {
                "role": "assistant",
                "content": message.content,
            }
            openai_tool_calls = message.additional_kwargs.get("tool_calls")
            if not openai_tool_calls and message.tool_calls:
                openai_tool_calls = [
                    {
                        "id": tc.get("id"),
                        "type": "function",
                        "function": {
                            "name": tc.get("name"),
                            "arguments": json.dumps(tc.get("args") or {}, ensure_ascii=False),
                        },
                    }
                    for tc in message.tool_calls
                ]
            if openai_tool_calls:
                payload["tool_calls"] = openai_tool_calls
            return payload
        raise ValueError(f"unsupported message type: {type(message)}")

    def _to_langchain_tool_calls(self, raw_tool_calls: Any) -> List[Dict[str, Any]]:
        if not raw_tool_calls:
            return []
        result: List[Dict[str, Any]] = []
        for item in raw_tool_calls:
            function_obj = item.get("function", {}) if isinstance(item, dict) else {}
            arguments_raw = function_obj.get("arguments", "{}")
            parsed_args: Dict[str, Any]
            if isinstance(arguments_raw, str):
                try:
                    loaded = json.loads(arguments_raw)
                    if isinstance(loaded, dict):
                        parsed_args = loaded
                    else:
                        parsed_args = {"value": loaded}
                except json.JSONDecodeError:
                    parsed_args = {"raw_arguments": arguments_raw}
            elif isinstance(arguments_raw, dict):
                parsed_args = arguments_raw
            else:
                parsed_args = {"value": arguments_raw}
            result.append(
                {
                    "name": function_obj.get("name"),
                    "args": parsed_args,
                    "id": item.get("id"),
                    "type": "tool_call",
                }
            )
        return result

    def _merge_extrabody(self, first: Any, second: Any) -> Optional[Dict[str, Any]]:
        merged: Dict[str, Any] = {}
        for value in [first, second]:
            if isinstance(value, dict):
                merged.update(value)
        if not merged:
            return None
        return merged
