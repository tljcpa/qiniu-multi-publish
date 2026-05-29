"""后端 API 测试。

/platforms 与 /adapt 的离线测试用 TestClient + monkeypatch 假 provider，不打网络。
另有一个带 key 的 live 测试验证端到端。
"""

import os

import pytest
from fastapi.testclient import TestClient

import app.main as main
from app.main import app
from tests.adapter_contract import FakeProvider

client = TestClient(app)


def test_platforms_lists_four():
    """4 个平台 adapter 应全部出现在 /platforms。"""
    resp = client.get("/platforms")
    assert resp.status_code == 200
    names = {p["name"] for p in resp.json()}
    assert {"wechat", "zhihu", "bilibili", "xhs"}.issubset(names)


def test_root_reports_platforms():
    body = client.get("/").json()
    assert "wechat" in body["platforms"]


def test_adapt_with_fake_provider(monkeypatch):
    """/adapt 用假 provider：应为每个目标平台返回适配结果与跳转意图。"""
    payload = {
        "title": "适配标题", "content": "适配正文",
        "summary": "摘要", "hashtags": ["甲", "乙"],
    }
    monkeypatch.setattr(main, "get_provider", lambda *a, **k: FakeProvider(payload))

    resp = client.post("/adapt", json={
        "content": {"title": "原标题", "body_md": "原文正文", "tags": ["x"]},
        "platforms": ["wechat", "xhs"],
    })
    assert resp.status_code == 200
    results = resp.json()["results"]
    assert len(results) == 2
    by_name = {r["platform"]: r for r in results}
    assert by_name["wechat"]["title"] == "适配标题"
    # 跳转意图：剪贴板非空 + 跳转 URL 指向对应平台
    assert by_name["wechat"]["publish_intent"]["clipboard"]
    assert by_name["wechat"]["publish_intent"]["url"].startswith("https://mp.weixin.qq.com")
    assert by_name["xhs"]["publish_intent"]["url"].startswith("https://creator.xiaohongshu.com")
    # 无指定 error
    assert by_name["wechat"]["error"] is None


def test_adapt_empty_platforms_means_all(monkeypatch):
    """platforms 为空表示适配到全部已注册平台。"""
    payload = {"title": "t", "content": "c", "summary": "", "hashtags": []}
    monkeypatch.setattr(main, "get_provider", lambda *a, **k: FakeProvider(payload))
    resp = client.post("/adapt", json={
        "content": {"title": "原", "body_md": "正文", "tags": []},
    })
    results = resp.json()["results"]
    assert len(results) >= 4


def test_adapt_unknown_platform_returns_error(monkeypatch):
    """未知平台不抛 500，而是在该平台结果里带 error。"""
    payload = {"title": "t", "content": "c", "summary": "", "hashtags": []}
    monkeypatch.setattr(main, "get_provider", lambda *a, **k: FakeProvider(payload))
    resp = client.post("/adapt", json={
        "content": {"title": "原", "body_md": "正文", "tags": []},
        "platforms": ["nope"],
    })
    assert resp.status_code == 200
    assert resp.json()["results"][0]["error"] is not None


def test_models_lists_deepseek():
    """GET /models 至少包含两个 DeepSeek 选项。"""
    resp = client.get("/models")
    assert resp.status_code == 200
    models = resp.json()
    pairs = {(m["provider"], m["model"]) for m in models}
    assert ("deepseek", "deepseek-chat") in pairs
    assert ("deepseek", "deepseek-reasoner") in pairs


def test_compare_with_fake_provider(monkeypatch):
    """/compare 用假 provider：单平台、两个模型变体应各返回结果与耗时。"""
    payload = {"title": "对比标题", "content": "对比正文", "summary": "", "hashtags": []}
    monkeypatch.setattr(main, "get_provider", lambda *a, **k: FakeProvider(payload))
    resp = client.post("/compare", json={
        "content": {"title": "原", "body_md": "正文", "tags": []},
        "platform": "wechat",
        "variants": [
            {"label": "A", "provider": "deepseek", "model": "deepseek-chat"},
            {"label": "B", "provider": "deepseek", "model": "deepseek-reasoner"},
        ],
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["platform"] == "wechat"
    assert len(body["variants"]) == 2
    for v in body["variants"]:
        assert v["result"]["title"] == "对比标题"
        assert v["latency_ms"] >= 0


def test_compare_default_variants(monkeypatch):
    """variants 为空时应使用默认两个模型对比。"""
    payload = {"title": "t", "content": "c", "summary": "", "hashtags": []}
    monkeypatch.setattr(main, "get_provider", lambda *a, **k: FakeProvider(payload))
    resp = client.post("/compare", json={
        "content": {"title": "原", "body_md": "正文", "tags": []},
        "platform": "xhs",
    })
    assert resp.status_code == 200
    assert len(resp.json()["variants"]) == 2


@pytest.mark.skipif(
    not os.getenv("DEEPSEEK_API_KEY"),
    reason="未设置 DEEPSEEK_API_KEY，跳过真实 /compare live",
)
def test_compare_live():
    """真连：公众号用两个 DeepSeek 模型对比。"""
    resp = client.post("/compare", json={
        "content": {"title": "远程办公真的更高效吗", "body_md": "省通勤但增沟通成本，关键在异步协作。", "tags": ["效率"]},
        "platform": "wechat",
        "variants": [
            {"label": "Chat", "provider": "deepseek", "model": "deepseek-chat"},
            {"label": "Reasoner", "provider": "deepseek", "model": "deepseek-reasoner"},
        ],
    })
    assert resp.status_code == 200
    variants = resp.json()["variants"]
    assert len(variants) == 2
    for v in variants:
        assert v["result"]["error"] is None
        assert v["result"]["title"]
        assert v["latency_ms"] > 0


@pytest.mark.skipif(
    not os.getenv("DEEPSEEK_API_KEY"),
    reason="未设置 DEEPSEEK_API_KEY，跳过真实 /adapt live",
)
def test_adapt_live_deepseek():
    """真连 DeepSeek，把一篇内容适配到公众号 + 小红书。"""
    resp = client.post("/adapt", json={
        "content": {
            "title": "远程办公真的更高效吗",
            "body_md": "远程办公省通勤但增沟通成本，关键在异步协作与文档文化。",
            "tags": ["远程办公", "效率"],
        },
        "platforms": ["wechat", "xhs"],
    })
    assert resp.status_code == 200
    results = {r["platform"]: r for r in resp.json()["results"]}
    assert results["wechat"]["title"] and results["wechat"]["error"] is None
    assert results["xhs"]["error"] is None
