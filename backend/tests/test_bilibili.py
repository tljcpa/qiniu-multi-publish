"""B 站 adapter 测试：统一契约 + 可选 live 适配。"""

import os

import pytest

from adapters.base import get_adapter
from adapters.bilibili import BilibiliAdapter
from tests.adapter_contract import SAMPLE, run_contract


def test_bilibili_contract():
    run_contract(BilibiliAdapter())


def test_bilibili_registered():
    adapter = get_adapter("bilibili")
    assert adapter.display_name == "B站"
    assert adapter.editor_url.startswith("https://member.bilibili.com")


def test_bilibili_style_prompt_mentions_interaction():
    prompt = BilibiliAdapter().style_prompt()
    assert "三连" in prompt


@pytest.mark.skipif(
    not os.getenv("DEEPSEEK_API_KEY"),
    reason="未设置 DEEPSEEK_API_KEY，跳过真实 LLM 适配 smoke",
)
def test_bilibili_live_adapt():
    from app.llm_provider import get_provider

    result = BilibiliAdapter().adapt(SAMPLE, get_provider("deepseek"))
    assert result.platform == "bilibili"
    assert result.title and result.content
