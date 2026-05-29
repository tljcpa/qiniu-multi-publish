"""LLM Provider 抽象层测试。

- 单元测试用 fake client 注入，不打网络，保证 main 始终可跑。
- 真连 DeepSeek 的 smoke 测试在无 DEEPSEEK_API_KEY 时自动 skip。
"""

import os
import types

import pytest

from app.llm_provider import (
    LLMError,
    _OpenAICompatProvider,
    get_provider,
)


def _make_resp(content):
    """构造一个形似 OpenAI 响应的对象（只含被用到的字段）。"""
    message = types.SimpleNamespace(content=content)
    choice = types.SimpleNamespace(message=message)
    return types.SimpleNamespace(choices=[choice])


class _FakeCompletions:
    """可编程的 fake：按预设的返回内容序列逐次响应。"""

    def __init__(self, contents):
        self._contents = list(contents)
        self.calls = []

    def create(self, **kwargs):
        # 记录调用参数，便于断言（如 response_format 是否被传入）
        self.calls.append(kwargs)
        content = self._contents.pop(0)
        return _make_resp(content)


class _FakeClient:
    def __init__(self, contents):
        self.chat = types.SimpleNamespace(completions=_FakeCompletions(contents))


def test_chat_returns_text():
    client = _FakeClient(["你好世界"])
    provider = _OpenAICompatProvider(client, "fake-model", "fake")
    out = provider.chat([{"role": "user", "content": "hi"}])
    assert out == "你好世界"


def test_chat_json_parses_object():
    client = _FakeClient(['{"title": "标题", "ok": true}'])
    provider = _OpenAICompatProvider(client, "fake-model", "fake")
    out = provider.chat_json([{"role": "user", "content": "给我 json"}])
    assert out == {"title": "标题", "ok": True}
    # JSON mode 必须传 response_format
    assert client.chat.completions.calls[0]["response_format"] == {"type": "json_object"}


def test_chat_json_retries_then_succeeds():
    # 第一次返回坏 JSON，第二次返回好 JSON，应在重试后成功
    client = _FakeClient(["not json", '{"v": 1}'])
    provider = _OpenAICompatProvider(client, "fake-model", "fake")
    out = provider.chat_json([{"role": "user", "content": "json"}], max_retries=2)
    assert out == {"v": 1}
    assert len(client.chat.completions.calls) == 2


def test_chat_json_raises_after_exhausting_retries():
    client = _FakeClient(["bad", "still bad"])
    provider = _OpenAICompatProvider(client, "fake-model", "fake")
    with pytest.raises(LLMError):
        provider.chat_json([{"role": "user", "content": "json"}], max_retries=1)


def test_get_provider_unknown_raises():
    with pytest.raises(LLMError):
        get_provider("no-such-backend")


def test_get_provider_azure_accepts_model_kwarg():
    """get_provider('azure', model=...) 的 kwarg 必须能传给 AzureProvider。

    回归测试：曾因 AzureProvider 形参名是 deployment 而非 model，导致
    /compare 走 Azure 时报 TypeError。现在应在无 key 时抛 LLMError（配置缺失），
    而不是 TypeError（参数不匹配）。
    """
    if os.getenv("AZURE_OPENAI_API_KEY") and os.getenv("AZURE_OPENAI_ENDPOINT"):
        # 有 key：应能正常构造
        provider = get_provider("azure", model="some-deployment")
        assert provider.name == "azure"
    else:
        # 无 key：应是 LLMError，绝不能是 TypeError
        with pytest.raises(LLMError):
            get_provider("azure", model="some-deployment")


@pytest.mark.skipif(
    not os.getenv("DEEPSEEK_API_KEY"),
    reason="未设置 DEEPSEEK_API_KEY，跳过真实联网 smoke 测试",
)
def test_deepseek_live_chat_json():
    """真连 DeepSeek：要求返回严格 JSON。仅在本地有 key 时运行。"""
    provider = get_provider("deepseek")
    out = provider.chat_json([
        {"role": "user", "content": "用 json 返回 {\"answer\": 1+1 的结果}"}
    ])
    assert isinstance(out, dict)
    assert "answer" in out
