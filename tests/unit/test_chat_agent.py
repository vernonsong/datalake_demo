#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.agents.chat_agent import ChatAgent


class _TokenMessage:
    def __init__(self, content):
        self.content = content


class _FakeAgent:
    def __init__(self):
        self.invoke_thread_id = None
        self.stream_thread_id = None

    def invoke(self, payload, config):
        self.invoke_thread_id = config["configurable"]["thread_id"]
        return {"messages": [{"content": "ok"}]}

    def stream(self, payload, config, stream_mode):
        self.stream_thread_id = config["configurable"]["thread_id"]
        yield "values", {"todos": [{"content": "历史任务", "status": "completed"}], "messages": []}
        yield "messages", (_TokenMessage("你好"), {"langgraph_node": "agent"})


class TestChatAgent(unittest.TestCase):
    def test_chat_generate_thread_id_when_missing(self):
        fake_agent = _FakeAgent()
        chat_agent = ChatAgent(agent=fake_agent)
        result = chat_agent.chat(user_id="u1", message="hello", conv_id=None)
        self.assertTrue(result["conversation_id"])
        self.assertNotEqual(result["conversation_id"], "default")
        self.assertEqual(fake_agent.invoke_thread_id, result["conversation_id"])

    def test_chat_use_provided_thread_id(self):
        fake_agent = _FakeAgent()
        chat_agent = ChatAgent(agent=fake_agent)
        result = chat_agent.chat(user_id="u1", message="hello", conv_id="conv_x")
        self.assertEqual(result["conversation_id"], "conv_x")
        self.assertEqual(fake_agent.invoke_thread_id, "conv_x")

    def test_chat_stream_not_emit_initial_history_todos(self):
        fake_agent = _FakeAgent()
        chat_agent = ChatAgent(agent=fake_agent)
        events = list(chat_agent.chat_stream(user_id="u1", message="你好", conv_id=None))
        todo_events = [e for e in events if e.get("type") == "todos"]
        token_events = [e for e in events if e.get("type") == "token"]
        self.assertEqual(len(todo_events), 0)
        self.assertGreaterEqual(len(token_events), 1)
        self.assertTrue(fake_agent.stream_thread_id)
        self.assertNotEqual(fake_agent.stream_thread_id, "default")


if __name__ == "__main__":
    unittest.main()
