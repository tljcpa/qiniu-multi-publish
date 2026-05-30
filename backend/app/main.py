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
import json
import time

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from app import __version__
from app.config import settings
from app.schemas import (
    AdaptRequest,
    AdaptResponse,
    CompareRequest,
    CompareResponse,
    CompareVariant,
    CompareVariantResult,
    IdeasRequest,
    IdeasResponse,
    ModelOption,
    PlatformInfo,
    PlatformResult,
    PlatformScore,
    PublishIntent,
    StrategyRequest,
    StrategyResponse,
)

# 导入 adapters 包触发所有平台 adapter 的自注册（@register 生效）
import adapters  # noqa: F401
from adapters.base import AdaptedResult, PlatformAdapter, all_adapters, get_adapter, platform_names
from app.llm_provider import LLMError, get_provider
from app.ratelimit import cost_rate_limit
from app.strategy import recommend_platforms
from app.streaming import build_stream_messages, parse_streamed

app = FastAPI(
    title="多平台内容发布工具 API",
    description="一份内容自动适配多平台格式与风格 - 适配 / 预览 / 复制 / 跳转",
    version=__version__,
)

# CORS：生产前端与后端同源（经 Caddy），CORS 仅对开发/外部调用生效。
# 收敛到已知来源而非通配，避免任意站点借我们的后端消耗 LLM 配额。
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://publish.qiniu.zdwktlj.top",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def _require_nonempty(content) -> None:
    """拒绝标题与正文同时为空的请求（API 层守卫，前端之外也兜底）。"""
    if not content.title.strip() and not content.body_md.strip():
        raise HTTPException(status_code=400, detail="标题与正文不能同时为空")


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


@app.post("/adapt", response_model=AdaptResponse, dependencies=[Depends(cost_rate_limit)])
async def adapt(req: AdaptRequest):
    """把一份内容并发适配到多个平台。

    部分平台失败不影响其它平台（该平台 result.error 非空）。
    """
    _require_nonempty(req.content)
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


@app.post("/compare", response_model=CompareResponse, dependencies=[Depends(cost_rate_limit)])
async def compare(req: CompareRequest):
    """同一平台、多个模型并发适配，返回各自结果与耗时，供用户对比挑选（亮点6）。"""
    _require_nonempty(req.content)
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


@app.post("/strategy", response_model=StrategyResponse, dependencies=[Depends(cost_rate_limit)])
async def strategy(req: StrategyRequest):
    """发布策略 Agent：判断这段内容该发哪些平台，给每个平台契合度分 + 理由（创新）。"""
    _require_nonempty(req.content)
    try:
        provider = get_provider(req.provider, **({"model": req.model} if req.model else {}))
    except LLMError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    scores = await asyncio.to_thread(recommend_platforms, req.content, provider, all_adapters())
    return StrategyResponse(scores=[PlatformScore(**s) for s in scores])


@app.post("/ideas", response_model=IdeasResponse, dependencies=[Depends(cost_rate_limit)])
async def ideas(req: IdeasRequest):
    """为单个平台生成原生标题/话题标签/封面文案建议（不改写正文，创新）。"""
    _require_nonempty(req.content)
    try:
        adapter = get_adapter(req.platform)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    try:
        provider = get_provider(req.provider, **({"model": req.model} if req.model else {}))
        result = await asyncio.to_thread(adapter.generate_ideas, req.content, provider)
    except Exception as exc:  # noqa: BLE001  失败时回传 error 字段，不抛 500
        return IdeasResponse(
            platform=req.platform, display_name=adapter.display_name,
            titles=[], hashtags=[], cover_copy=[], error=f"生成失败: {exc}",
        )
    return IdeasResponse(
        platform=result.platform,
        display_name=adapter.display_name,
        titles=result.titles,
        hashtags=result.hashtags,
        cover_copy=result.cover_copy,
        model=result.model,
    )


def _sse(payload: dict) -> str:
    """把一个事件序列化成 SSE 数据帧。"""
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


@app.post("/adapt/stream", dependencies=[Depends(cost_rate_limit)])
async def adapt_stream(req: AdaptRequest):
    """流式适配：多平台并发"打字机"，通过 SSE 边生成边推送（亮点：观感）。

    每平台一个线程跑 provider.chat_stream，经队列汇流到单条 SSE 响应。
    事件类型：meta（平台元信息）/ delta（增量文本）/ done（结构化结果）/ error / all_done。
    """
    _require_nonempty(req.content)
    targets = req.platforms
    if not targets:
        targets = platform_names()

    async def event_gen():
        # provider 初始化失败：对每个平台发 error 后收尾
        try:
            provider = get_provider(req.provider, **({"model": req.model} if req.model else {}))
        except LLMError as exc:
            for name in targets:
                yield _sse({"type": "error", "platform": name, "error": str(exc)})
            yield _sse({"type": "all_done"})
            return

        # 先发各平台元信息，前端据此先把空手机壳占位排好
        valid: list[str] = []
        for name in targets:
            try:
                adapter = get_adapter(name)
            except KeyError as exc:
                yield _sse({"type": "error", "platform": name, "error": str(exc)})
                continue
            valid.append(name)
            yield _sse({
                "type": "meta",
                "platform": name,
                "display_name": adapter.display_name,
                "preview_template": adapter.preview_template(),
            })

        queue: asyncio.Queue = asyncio.Queue()
        loop = asyncio.get_running_loop()

        def worker(name: str):
            # 在线程里跑同步流式生成器，逐块经 call_soon_threadsafe 推入队列
            try:
                adapter = get_adapter(name)
                messages = build_stream_messages(adapter, req.content)
                buf: list[str] = []
                for delta in provider.chat_stream(messages):
                    buf.append(delta)
                    loop.call_soon_threadsafe(
                        queue.put_nowait, {"type": "delta", "platform": name, "text": delta}
                    )
                result = parse_streamed(name, "".join(buf), getattr(provider, "name", ""))
                payload = _build_result(adapter, result).model_dump()
                loop.call_soon_threadsafe(
                    queue.put_nowait, {"type": "done", "platform": name, "result": payload}
                )
            except Exception as exc:  # noqa: BLE001  单平台失败不拖垮整体
                loop.call_soon_threadsafe(
                    queue.put_nowait, {"type": "error", "platform": name, "error": f"适配失败: {exc}"}
                )
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, {"type": "_done", "platform": name})

        for name in valid:
            loop.run_in_executor(None, worker, name)

        remaining = len(valid)
        while remaining > 0:
            evt = await queue.get()
            if evt["type"] == "_done":
                remaining -= 1
                continue
            yield _sse(evt)
        yield _sse({"type": "all_done"})

    # text/event-stream + 关闭代理缓冲
    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
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
