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
import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.config import settings
from app.schemas import (
    AdaptRequest,
    AdaptResponse,
    CompareRequest,
    CompareResponse,
    CompareVariant,
    CompareVariantResult,
    ModelOption,
    PlatformInfo,
    PlatformResult,
    PublishIntent,
)

# 导入 adapters 包触发所有平台 adapter 的自注册（@register 生效）
import adapters  # noqa: F401
from adapters.base import AdaptedResult, PlatformAdapter, all_adapters, get_adapter, platform_names
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
        return _build_result(adapter, result)

    results = await asyncio.gather(*[adapt_one(n) for n in targets])
    return AdaptResponse(results=list(results))


def _build_result(adapter: PlatformAdapter, result: AdaptedResult) -> PlatformResult:
    """把适配结果 + adapter 渲染/跳转意图组装成对外 PlatformResult。"""
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


@app.get("/models", response_model=list[ModelOption])
def list_models():
    """列出当前可用的 LLM 模型（按已配置的 key 动态返回），供前端多模型对比选择。"""
    options: list[ModelOption] = [
        ModelOption(label="DeepSeek Chat", provider="deepseek", model="deepseek-chat"),
        ModelOption(label="DeepSeek Reasoner", provider="deepseek", model="deepseek-reasoner"),
    ]
    # 仅在 Azure 配置齐全时才暴露，避免前端选了用不了
    if settings.azure_openai_api_key and settings.azure_openai_endpoint:
        options.append(ModelOption(
            label="GPT-4.1-mini (Azure)",
            provider="azure",
            model=settings.azure_openai_deployment,
        ))
    return options


@app.post("/compare", response_model=CompareResponse)
async def compare(req: CompareRequest):
    """同一平台、多个模型并发适配，返回各自结果与耗时，供用户对比挑选（亮点6）。"""
    adapter = get_adapter(req.platform)

    variants = req.variants
    if not variants:
        # 默认对比：DeepSeek Chat vs Azure（无 Azure 则退化为 DeepSeek Chat vs Reasoner）
        variants = [CompareVariant(label="DeepSeek Chat", provider="deepseek", model="deepseek-chat")]
        if settings.azure_openai_api_key and settings.azure_openai_endpoint:
            variants.append(CompareVariant(label="GPT-4.1-mini (Azure)", provider="azure", model=settings.azure_openai_deployment))
        else:
            variants.append(CompareVariant(label="DeepSeek Reasoner", provider="deepseek", model="deepseek-reasoner"))

    async def run_variant(v: CompareVariant) -> CompareVariantResult:
        started = time.monotonic()
        try:
            provider = get_provider(v.provider, **({"model": v.model} if v.model else {}))
            result = await asyncio.to_thread(adapter.adapt, req.content, provider)
            built = _build_result(adapter, result)
        except Exception as exc:  # noqa: BLE001  单模型失败不拖垮对比
            built = _error_result(req.platform, f"适配失败: {exc}", adapter.display_name)
        latency = int((time.monotonic() - started) * 1000)
        return CompareVariantResult(
            label=v.label,
            provider=v.provider,
            model=v.model or "",
            latency_ms=latency,
            result=built,
        )

    variant_results = await asyncio.gather(*[run_variant(v) for v in variants])
    return CompareResponse(
        platform=req.platform,
        display_name=adapter.display_name,
        variants=list(variant_results),
    )


def _error_result(name: str, message: str, display_name: str = "") -> PlatformResult:
    """构造一个表示失败的平台结果。"""
    return PlatformResult(
        platform=name,
        display_name=display_name or name,
        title="",
        content="",
        error=message,
    )
