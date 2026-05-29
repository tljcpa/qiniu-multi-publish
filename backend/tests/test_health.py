"""骨架冒烟测试：确认应用可启动、基础路由返回正常。

每个 PR 合并后 main 必须可运行（BRIEF §2.3），这组测试是最低保障。
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root():
    """根路由返回服务信息，且体现产品定位。"""
    resp = client.get("/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["service"] == "multi-publish"
    assert "positioning" in body


def test_health():
    """健康检查返回 ok。"""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
