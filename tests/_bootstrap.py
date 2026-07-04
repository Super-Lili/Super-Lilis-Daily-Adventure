"""Shared test bootstrap: make src/ importable and mock the openai SDK
so no test ever needs a network connection or an API key."""

import os
import sys
import types
from pathlib import Path

SRC = str(Path(__file__).resolve().parent.parent / "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

os.environ.setdefault("DEEPSEEK_API_KEY", "test-key")
os.environ.setdefault("QWEN_API_KEY", "test-key")
os.environ.setdefault("GITHUB_TOKEN", "test-token")


class _Msg:
    def __init__(self, content):
        self.content = content


class _Choice:
    def __init__(self, content):
        self.message = _Msg(content)
        self.finish_reason = "stop" if content else "length"


class _Resp:
    def __init__(self, content):
        self.choices = [_Choice(content)]


def make_scripted_client(script):
    """Return a fake OpenAI-style client that replays `script` per call:
    each item is a string (content), None (empty response), or 'ERR' (raises)."""
    calls = iter(script)

    class _Completions:
        @staticmethod
        def create(**kwargs):
            item = next(calls)
            if item == "ERR":
                raise RuntimeError("scripted failure")
            return _Resp(item)

    class _Chat:
        completions = _Completions()

    class _Client:
        chat = _Chat()

    return _Client()


if "openai" not in sys.modules:
    _fake = types.ModuleType("openai")

    class _FakeOpenAI:  # constructor-compatible stand-in
        def __init__(self, **kwargs):
            pass

    _fake.OpenAI = _FakeOpenAI
    sys.modules["openai"] = _fake
