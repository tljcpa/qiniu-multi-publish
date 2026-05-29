"""FastAPI 应用入口。

路由：
- GET  /              服务信息
- GET  /health        健康检查
- GET  /platforms     列出所有已注册平台（前端据此渲染平台列表）
- POST /adapt         把一份内容并发适配到多个平台

保持 main 分支始终可运行（见 BRIEF §2.3）。
真正的服务运行/联调在 Azure VM 上做，本机只跑进程内单元测试。
"""

from __future__ import annotations

import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.config import settings
from app.schemas import (
    AdaptRequest,
    AdaptResponse,
    PlatformInfo,
    PlatformResult,
    PublishIntent,
)

# 导入 adapters 包触发所有平台 adapter 的自注册（@register 生效）
import adapters  # noqa: F401
from adapters.base import all_adapters, get_adapter, platform_names
from app.llm_provider import LLMError, get_provider

app = FastAPI(
    title="多平台内容发布工具 API",
    description="一份内容自动适配多平台格式与风格 - 适配 / 预览 / 复制 / 跳转",
    version=__version__,
)

# 允许前端跨域访问（前端与后端可能分端口/分域名部署）。demo 优先，放开来源。
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    """根路由：返回服务基本信息。"""
    return {
        "service": settings.app_name,
        "version": __version__,
        "positioning": "适配 -> 预览 -> 复制 -> 跳转，不假装能发",
        "platforms": platform_names(),
    }


@app.get("/health")
def health():
    """健康检查：部署后供探活，也供测试断言。"""
    return {"status": "ok"}


@app.get("/platforms", response_model=list[PlatformInfo])
def list_platforms():
    """列出所有已注册平台。新增 adapter 后自动出现，无需改动本路由。"""
    infos: list[PlatformInfo] = []
    for adapter in all_adapters():
        infos.append(PlatformInfo(
            name=adapter.name,
            display_name=adapter.display_name,
            editor_url=adapter.editor_url,
            preview_template=adapter.preview_template(),
            extension_guide=adapter.extension_guide(),
        ))
    return infos


@app.post("/adapt", response_model=AdaptResponse)
async def adapt(req: AdaptRequest):
    """把一份内容并发适配到多个平台。

    部分平台失败不影响其它平台（该平台 result.error 非空）。
    """
    # 目标平台：未指定则适配到全部
    targets = req.platforms
    if not targets:
        targets = platform_names()

    # 复用同一个 provider 实例（构造一次，避免每平台重建 client）
    try:
        provider = get_provider(req.provider, **({"model": req.model} if req.model else {}))
    except LLMError as exc:
        # provider 初始化失败（如未配 key）：所有平台统一返回该错误
        return AdaptResponse(results=[
            _error_result(name, str(exc)) for name in targets
        ])

    async def adapt_one(name: str) -> PlatformResult:
        try:
            adapter = get_adapter(name)
        except KeyError as exc:
            return _error_result(name, str(exc))
        try:
            # adapter.adapt 是同步阻塞调用，丢到线程池里并发跑，避免阻塞事件循环
            result = await asyncio.to_thread(adapter.adapt, req.content, provider)
        except Exception as exc:  # noqa: BLE001  单平台失败不拖垮整体
            return _error_result(name, f"适配失败: {exc}", adapter.display_name)
        intent = adapter.publish_intent(result)
        return PlatformResult(
            platform=result.platform,
            display_name=adapter.display_name,
            title=result.title,
            content=result.content,
            summary=result.summary,
            hashtags=result.hashtags,
            model=result.model,
            preview_template=adapter.preview_template(),
            formatted=adapter.format_content(result),
            publish_intent=PublishIntent(**intent),
        )

    results = await asyncio.gather(*[adapt_one(n) for n in targets])
    return AdaptResponse(results=list(results))


def _error_result(name: str, message: str, display_name: str = "") -> PlatformResult:
    """构造一个表示失败的平台结果。"""
    return PlatformResult(
        platform=name,
        display_name=display_name or name,
        title="",
        content="",
        error=message,
    )
