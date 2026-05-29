"""小红书 adapter 测试：统一契约 + 覆写行为 + 可选 live 适配。"""

import os

import pytest

from adapters.base import AdaptedResult, get_adapter
from adapters.xhs import XhsAdapter
from tests.adapter_contract import SAMPLE, run_contract


def test_xhs_contract():
    run_contract(XhsAdapter())


def test_xhs_registered():
    adapter = get_adapter("xhs")
    assert adapter.display_name == "小红书"
    assert adapter.editor_url.startswith("https://creator.xiaohongshu.com")


def test_xhs_schema_has_cover_alt():
    """小红书覆写了 schema，应包含 cover_alt 字段。"""
    assert "cover_alt" in XhsAdapter().output_schema()


def test_xhs_format_puts_hashtags_at_end():
    adapter = XhsAdapter()
    result = AdaptedResult(
        platform="xhs", title="标题✨", content="正文内容",
        hashtags=["护肤", "学生党"],
    )
    text = adapter.format_content(result)
    assert text.strip().endswith("#护肤 #学生党")


@pytest.mark.skipif(
    not os.getenv("DEEPSEEK_API_KEY"),
    reason="未设置 DEEPSEEK_API_KEY，跳过真实 LLM 适配 smoke",
)
def test_xhs_live_adapt():
    from app.llm_provider import get_provider

    result = XhsAdapter().adapt(SAMPLE, get_provider("deepseek"))
    assert result.platform == "xhs"
    assert result.title and result.content
    # 小红书应产出多个话题标签
    assert len(result.hashtags) >= 3
