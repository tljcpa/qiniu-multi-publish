"""可复用的 Adapter 契约测试工具。

每个平台 adapter（PR5-PR8）的测试都 import `run_contract`，
对自己跑同一组契约断言——这就是 BRIEF §5.3 要求的"统一测试模板"。
本文件无 test_ 函数，pytest 不会把它当测试用例收集。
"""

from adapters.base import AdaptedResult, ContentInput, PlatformAdapter

# 所有 adapter 共用的示例输入
SAMPLE = ContentInput(
    title="如何高效学习一门新技能",
    body_md="# 引言\n\n学习新技能需要方法。\n\n## 第一步\n\n刻意练习很重要。",
    tags=["学习方法", "成长"],
)


class FakeProvider:
    """假的 LLMProvider：不打网络，返回预设 JSON，用于契约测试。"""

    name = "fake"

    def __init__(self, payload: dict):
        self._payload = payload

    def chat(self, *args, **kwargs):
        return ""

    def chat_stream(self, *args, **kwargs):
        yield ""

    def chat_json(self, messages, **kwargs):
        # 顺带断言：adapter 必须把 style_prompt 放进 system 消息
        assert messages[0]["role"] == "system"
        assert messages[0]["content"].strip()
        return self._payload


def run_contract(adapter: PlatformAdapter, payload: dict | None = None) -> AdaptedResult:
    """对任意 adapter 跑统一契约，返回适配结果以便调用方追加断言。"""
    # 1. 身份字段齐全
    assert adapter.name, "name 不能为空"
    assert adapter.display_name, "display_name 不能为空"
    assert adapter.editor_url.startswith("http"), "editor_url 必须是 URL"

    # 2. 风格 prompt 非空（风格适配的灵魂）
    assert adapter.style_prompt().strip(), "style_prompt 不能为空"

    # 3. adapt 编排返回合法 AdaptedResult
    payload = payload or {
        "title": "适配后的标题",
        "content": "适配后的正文内容。",
        "summary": "一句话摘要",
        "hashtags": ["标签一", "标签二"],
    }
    provider = FakeProvider(payload)
    result = adapter.adapt(SAMPLE, provider)
    assert isinstance(result, AdaptedResult)
    assert result.platform == adapter.name
    assert result.title, "适配结果标题不能为空"
    assert result.content, "适配结果正文不能为空"

    # 4. publish_intent 含剪贴板内容 + 跳转 URL（产品定位 D-01）
    intent = adapter.publish_intent(result)
    assert intent["clipboard"].strip(), "clipboard 不能为空"
    assert intent["url"].startswith("http"), "跳转 url 必须是 URL"

    return result
