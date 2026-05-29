"""公众号 adapter 测试：跑统一契约 + 可选的真实 LLM 适配 smoke。"""

import os

import pytest

from adapters.base import get_adapter
from adapters.wechat import WeChatAdapter
from tests.adapter_contract import SAMPLE, run_contract


def test_wechat_contract():
    """公众号 adapter 通过统一契约。"""
    run_contract(WeChatAdapter())


def test_wechat_registered():
    """import 后应已自注册，可从注册表取到。"""
    adapter = get_adapter("wechat")
    assert adapter.display_name == "公众号"
    assert adapter.editor_url.startswith("https://mp.weixin.qq.com")


def test_wechat_style_prompt_mentions_key_rules():
    """风格 prompt 应体现公众号关键规则（段落短 / emoji 克制）。"""
    prompt = WeChatAdapter().style_prompt()
    assert "段落" in prompt
    assert "emoji" in prompt.lower()


@pytest.mark.skipif(
    not os.getenv("DEEPSEEK_API_KEY"),
    reason="未设置 DEEPSEEK_API_KEY，跳过真实 LLM 适配 smoke",
)
def test_wechat_live_adapt():
    """真连 DeepSeek 做一次公众号适配，验证端到端产出合法结果。"""
    from app.llm_provider import get_provider

    adapter = WeChatAdapter()
    result = adapter.adapt(SAMPLE, get_provider("deepseek"))
    assert result.platform == "wechat"
    assert result.title and result.content
    assert result.model == "deepseek"
