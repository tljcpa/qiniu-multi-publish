"""流式适配测试：parse_streamed 纯解析单测 + /adapt/stream SSE 端点（假流式 provider）。"""

import json

from fastapi.testclient import TestClient

import app.main as main
from app.main import app
from app.streaming import build_stream_messages, parse_streamed
from adapters.base import ContentInput
from adapters.wechat import WeChatAdapter

client = TestClient(app)


def test_parse_streamed_basic():
    text = "远程办公真的更高效吗\n\n第一段正文。\n\n第二段正文。\nTAGS: 效率, 远程办公, 职场"
    result = parse_streamed("wechat", text, "deepseek")
    assert result.platform == "wechat"
    assert result.title == "远程办公真的更高效吗"
    assert "第一段正文。" in result.content
    assert "TAGS" not in result.content
    assert result.hashtags == ["效率", "远程办公", "职场"]
    assert result.model == "deepseek"


def test_parse_streamed_chinese_colon_and_hash():
    text = "标题行\n正文。\nTAGS：#甲，#乙"
    result = parse_streamed("xhs", text, "azure")
    assert result.title == "标题行"
    assert result.hashtags == ["甲", "乙"]


def test_parse_streamed_no_tags():
    text = "只有标题\n\n正文内容\nTAGS:"
    result = parse_streamed("zhihu", text, "deepseek")
    assert result.title == "只有标题"
    assert result.hashtags == []
    assert "正文内容" in result.content


def test_build_stream_messages_uses_style_prompt():
    msgs = build_stream_messages(WeChatAdapter(), ContentInput(title="t", body_md="b", tags=["x"]))
    assert msgs[0]["role"] == "system"
    assert msgs[0]["content"]  # style_prompt 非空
    assert "TAGS:" in msgs[-1]["content"]  # 用户消息含格式说明


class _StreamFakeProvider:
    """假流式 provider：chat_stream 把约定格式文本分块吐出。"""

    name = "fake"

    def __init__(self, text: str):
        self._text = text

    def chat(self, *a, **k):
        return self._text

    def chat_json(self, *a, **k):
        return {}

    def chat_stream(self, messages, **k):
        # 按 8 字符一块吐，模拟流式
        for i in range(0, len(self._text), 8):
            yield self._text[i : i + 8]


def test_adapt_stream_sse(monkeypatch):
    """/adapt/stream 应产出 meta/delta/done/all_done 事件，且 done 里是解析后的结构化结果。"""
    text = "公众号标题\n\n正文一段。\nTAGS: 效率, 成长"
    monkeypatch.setattr(main, "get_provider", lambda *a, **k: _StreamFakeProvider(text))

    resp = client.post("/adapt/stream", json={
        "content": {"title": "原", "body_md": "正文", "tags": []},
        "platforms": ["wechat"],
    })
    assert resp.status_code == 200
    # 解析 SSE：收集所有 data 帧
    events = []
    for line in resp.text.splitlines():
        if line.startswith("data: "):
            events.append(json.loads(line[len("data: "):]))

    types = [e["type"] for e in events]
    assert "meta" in types
    assert "delta" in types
    assert "done" in types
    assert types[-1] == "all_done"

    done = next(e for e in events if e["type"] == "done")
    assert done["platform"] == "wechat"
    assert done["result"]["title"] == "公众号标题"
    assert done["result"]["hashtags"] == ["效率", "成长"]
    assert done["result"]["publish_intent"]["url"].startswith("https://mp.weixin.qq.com")
