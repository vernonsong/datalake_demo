import os
import sys
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from langchain_core.messages import AIMessage

from poc.langchain_nonopenai.chat_model import ProviderCompatibleChatModel


class TestProviderCompatibleChatModel(unittest.TestCase):
    def setUp(self):
        self.model = ProviderCompatibleChatModel(
            base_url="https://provider.example.com/chat/completions",
            model="provider-model",
            token_provider=lambda: "dynamic-token",
            timeout_seconds=20.0,
        )

    @patch("poc.langchain_nonopenai.chat_model.requests.post")
    def test_bind_tools_puts_tools_into_extrabody(self, mock_post: Mock):
        mock_resp = Mock()
        mock_resp.json.return_value = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "ok",
                    }
                }
            ]
        }
        mock_resp.raise_for_status.return_value = None
        mock_post.return_value = mock_resp

        def add(a: int, b: int) -> int:
            return a + b

        runnable = self.model.bind_tools([add])
        runnable.invoke("计算 1+2")

        kwargs = mock_post.call_args.kwargs
        payload = kwargs["json"]
        self.assertIn("extrabody", payload)
        self.assertIn("tools", payload["extrabody"])
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer dynamic-token")

    @patch("poc.langchain_nonopenai.chat_model.requests.post")
    def test_provider_tool_calls_convert_to_langchain_tool_calls(self, mock_post: Mock):
        mock_resp = Mock()
        mock_resp.json.return_value = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "",
                        "tool_calls": [
                            {
                                "id": "call_1",
                                "type": "function",
                                "function": {
                                    "name": "add",
                                    "arguments": "{\"a\":1,\"b\":2}",
                                },
                            }
                        ],
                    }
                }
            ]
        }
        mock_resp.raise_for_status.return_value = None
        mock_post.return_value = mock_resp

        result = self.model.invoke("算 1+2")
        self.assertIsInstance(result, AIMessage)
        self.assertEqual(result.tool_calls[0]["name"], "add")
        self.assertEqual(result.tool_calls[0]["args"]["a"], 1)
        self.assertEqual(result.tool_calls[0]["args"]["b"], 2)


if __name__ == "__main__":
    unittest.main()
