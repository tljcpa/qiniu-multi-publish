"""FastAPI 应用入口。

PR1 阶段只提供最小可运行骨架：根路由 + 健康检查。
真正的业务路由（POST /adapt、GET /preview/{platform} 等）在 PR10 接入。
保持 main 分支始终可运行（见 BRIEF §2.3）。
"""

from fastapi import FastAPI

from app import __version__
from app.config import settings

app = FastAPI(
    title="多平台内容发布工具 API",
    description="一份内容自动适配多平台格式与风格 - 适配 / 预览 / 复制 / 跳转",
    version=__version__,
)


@app.get("/")
def root():
    """根路由：返回服务基本信息，便于快速确认服务存活。"""
    return {
        "service": settings.app_name,
        "version": __version__,
        # 产品定位一句话，呼应 D-01：不做真发布
        "positioning": "适配 -> 预览 -> 复制 -> 跳转，不假装能发",
    }


@app.get("/health")
def health():
    """健康检查：部署后供 Caddy / 负载探活，也供测试断言。"""
    return {"status": "ok"}
