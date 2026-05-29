"""知乎 adapter 测试：统一契约 + 可选 live 适配。"""

import os

import pytest

from adapters.base import get_adapter
from adapters.zhihu import ZhihuAdapter
from tests.adapter_contract import SAMPLE, run_contract


def test_zhihu_contract():
    run_contract(ZhihuAdapter())


def test_zhihu_registered():
    adapter = get_adapter("zhihu")
    assert adapter.display_name == "知乎"
    assert adapter.editor_url.startswith("https://zhuanlan.zhihu.com")


def test_zhihu_style_prompt_mentions_reasoning():
    prompt = ZhihuAdapter().style_prompt()
    assert "严谨" in prompt or "论证" in prompt


@pytest.mark.skipif(
    not os.getenv("DEEPSEEK_API_KEY"),
    reason="未设置 DEEPSEEK_API_KEY，跳过真实 LLM 适配 smoke",
)
def test_zhihu_live_adapt():
    from app.llm_provider import get_provider

    result = ZhihuAdapter().adapt(SAMPLE, get_provider("deepseek"))
    assert result.platform == "zhihu"
    assert result.title and result.content
