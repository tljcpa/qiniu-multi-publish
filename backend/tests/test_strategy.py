"""发布策略 Agent 测试：平台档案 + 打分解析 + 创意生成（离线 + 可选 live）。"""

import os

import pytest

from adapters.base import ContentInput, PlatformIdeas, all_adapters, get_adapter
from app.strategy import recommend_platforms
from tests.adapter_contract import SAMPLE, FakeProvider


def test_every_adapter_has_strategy_profile():
    """每个平台都要有定位档案（新平台进入打分的前提）。"""
    for adapter in all_adapters():
        prof = adapter.strategy_profile()
        assert prof["content_types"]
        assert prof["ideal_length"]
        assert prof["tone"]


# 仅用 4 个真实平台（避免其它测试注册的 dummy adapter 干扰计数）
REAL = [get_adapter(n) for n in ("wechat", "zhihu", "bilibili", "xhs")]


def test_recommend_platforms_parse_and_fallback():
    """打分解析：阈值、降序、漏返回的平台兜底补齐。"""
    payload = {"scores": [
        {"platform": "zhihu", "score": 85, "reason": "深度论证适合"},
        {"platform": "wechat", "score": 70, "reason": "长文适合"},
        {"platform": "xhs", "score": 30, "reason": "太硬核不适合"},
        # bilibili 故意漏掉，应被兜底补上
    ]}
    results = recommend_platforms(SAMPLE, FakeProvider(payload), REAL)
    by = {r["platform"]: r for r in results}
    assert len(results) == 4  # 4 平台都在
    assert results[0]["platform"] == "zhihu"  # 降序，最高分在前
    assert by["zhihu"]["recommended"] is True
    assert by["wechat"]["recommended"] is True
    assert by["xhs"]["recommended"] is False
    assert by["bilibili"]["score"] == 0  # 兜底
    assert by["bilibili"]["recommended"] is False


def test_recommend_clamps_bad_score():
    payload = {"scores": [{"platform": "wechat", "score": 999, "reason": "x"}]}
    results = recommend_platforms(SAMPLE, FakeProvider(payload), all_adapters())
    assert {r["platform"]: r["score"] for r in results}["wechat"] == 100


def test_generate_ideas_coerces():
    """创意生成：标题/标签/封面文案，标签字符串归一为列表并去 #。"""
    payload = {
        "titles": ["标题A", "标题B", "标题C"],
        "hashtags": "#成长, 效率，#方法",
        "cover_copy": ["封面文案一"],
    }
    ideas = get_adapter("wechat").generate_ideas(
        ContentInput(title="t", body_md="b", tags=[]), FakeProvider(payload)
    )
    assert isinstance(ideas, PlatformIdeas)
    assert ideas.titles == ["标题A", "标题B", "标题C"]
    assert ideas.hashtags == ["成长", "效率", "方法"]
    assert ideas.cover_copy == ["封面文案一"]


@pytest.mark.skipif(not os.getenv("DEEPSEEK_API_KEY"), reason="无 key 跳过 live")
def test_strategy_live():
    from app.llm_provider import get_provider

    results = recommend_platforms(SAMPLE, get_provider("deepseek"), REAL)
    assert len(results) == 4
    assert all(0 <= r["score"] <= 100 for r in results)
