"""PlatformAdapter 抽象基类与注册表测试。

用一个 Dummy adapter 验证：默认实现可用、契约模板可跑、注册表行为正确。
"""

import pytest

from adapters.base import (
    AdaptedResult,
    ContentInput,
    PlatformAdapter,
    all_adapters,
    get_adapter,
    platform_names,
    register,
)
from tests.adapter_contract import FakeProvider, run_contract


@register
class _DummyAdapter(PlatformAdapter):
    """仅用于测试的最小 adapter：只实现必须的身份 + style_prompt。"""

    name = "dummy-test"
    display_name = "测试平台"
    editor_url = "https://example.com/write"

    def style_prompt(self) -> str:
        return "你是测试平台的编辑，请保持简洁。"


def test_dummy_passes_contract():
    """最小 adapter 应通过统一契约（证明默认实现足够用）。"""
    run_contract(_DummyAdapter())


def test_registry_get_and_list():
    """注册表可按 name 取实例，并出现在列表里。"""
    adapter = get_adapter("dummy-test")
    assert adapter.name == "dummy-test"
    assert "dummy-test" in platform_names()
    assert any(a.name == "dummy-test" for a in all_adapters())


def test_get_unknown_raises():
    with pytest.raises(KeyError):
        get_adapter("does-not-exist")


def test_register_without_name_raises():
    with pytest.raises(ValueError):
        @register
        class _NoName(PlatformAdapter):
            def style_prompt(self):
                return "x"


def test_default_format_content_includes_title_and_hashtags():
    """默认 format_content 应包含标题与 # 话题标签。"""
    adapter = _DummyAdapter()
    result = AdaptedResult(
        platform="dummy-test",
        title="标题",
        content="正文",
        hashtags=["甲", "乙"],
    )
    text = adapter.format_content(result)
    assert "标题" in text
    assert "#甲" in text and "#乙" in text


def test_hashtags_string_is_normalized():
    """LLM 把 hashtags 返回成字符串时，_to_result 应归一为列表。"""
    adapter = _DummyAdapter()
    payload = {
        "title": "T",
        "content": "C",
        "summary": "S",
        # 故意返回字符串形式，含中英文逗号与 # 前缀
        "hashtags": "#成长, 学习，#方法",
    }
    result = adapter.adapt(
        ContentInput(title="t", body_md="b", tags=[]),
        FakeProvider(payload),
    )
    assert result.hashtags == ["成长", "学习", "方法"]
