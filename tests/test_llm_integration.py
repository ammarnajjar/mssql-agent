import os
import json

import pytest

from agent import llm


class DummyResp:
    def __init__(self, content):
        self.choices = [{"message": {"content": content}}]


def test_call_llm_missing_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(llm.LLMError):
        llm.call_llm("sys", "user")


def test_call_llm_parsing(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test")

    def fake_create(**kwargs):
        return {"choices": [{"message": {"content": '{"sql": "SELECT 1;", "notes": "ok"}'}}]}

    # inject a fake openai module on the llm.openai reference
    class FakeOpenAI:
        def __init__(self):
            self.api_key = None

        class ChatCompletion:
            @staticmethod
            def create(**kwargs):
                return {"choices": [{"message": {"content": '{"sql": "SELECT 1;", "notes": "ok"}'}}]}

    monkeypatch.setattr(llm, "openai", FakeOpenAI())
    resp = llm.call_llm("sys", "user")
    assert "choices" in resp
