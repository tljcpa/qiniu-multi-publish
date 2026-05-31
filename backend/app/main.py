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
import io
import json
import time
import zipfile

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse

from app import __version__
from app.config import settings
from app.database import history_delete, history_list, history_save, init_db
from app.schemas import (
    AdaptRequest,
    AdaptResponse,
    CompareRequest,
    CompareResponse,
    CompareVariant,
    CompareVariantResult,
    DraftRequest,
    DraftResponse,
    ExportRequest,
    HistoryItem,
    HistoryListResponse,
    IdeasRequest,
    IdeasResponse,
    ModelOption,
    PlatformInfo,
    PlatformResult,
    PlatformScore,
    PublishIntent,
    SaveHistoryRequest,
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


@app.on_event("startup")
def startup() -> None:
    """应用启动时初始化数据库（建表幂等，已存在则跳过）。"""
    init_db()

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
    try:
        adapter = get_adapter(req.platform)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

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


# ---------------------- AI 起草管线 ----------------------

# 起草 prompt（喂给 DeepSeek，非密内容，只有用户输入的主题）
_DRAFT_SYSTEM = (
    "你是一名专业的内容创作者，擅长为多平台写出有观点、有案例的原创文章。"
    "请根据用户给出的主题，创作一篇 600-800 字的文章。"
    "结构要求：标题 + 正文（用 ## 分段，2-3 个段落）。"
    "语言：简体中文，文笔自然流畅，有明确观点。"
    "输出格式：只输出 JSON，字段为 title（字符串）、body_md（Markdown 字符串）、tags（字符串数组，3-5 个）。"
)

# 审核 prompt（喂给 DeepSeek，消耗少量 token 只做润色不重写）
_REVIEW_SYSTEM = (
    "你是内容编辑，职责是润色一篇初稿：修正语病、优化段落节奏、补充 1-2 个具体细节，"
    "但保留作者原有观点和结构，不大幅重写。"
    "输出格式：只输出 JSON，字段同输入：title、body_md、tags。"
)


@app.post("/draft", response_model=DraftResponse, dependencies=[Depends(cost_rate_limit)])
async def draft(req: DraftRequest):
    """AI 起草管线：DeepSeek 起草初稿，再由 DeepSeek 轻量润色。

    起草与润色分两步、低温润色不重写结构。
    """
    # Step 1：DeepSeek 起草（只传用户主题，无任何密钥或敏感信息）
    try:
        drafter = get_provider("deepseek")
    except LLMError as exc:
        raise HTTPException(status_code=503, detail=f"起草服务不可用: {exc}")

    draft_messages = [
        {"role": "system", "content": _DRAFT_SYSTEM},
        {"role": "user", "content": f"主题：{req.topic}"},
    ]
    try:
        raw = await asyncio.to_thread(drafter.chat_json, draft_messages, temperature=0.8)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"起草失败: {exc}")

    draft_title = str(raw.get("title", req.topic))
    draft_body = str(raw.get("body_md", ""))
    draft_tags: list[str] = [str(t) for t in raw.get("tags", [])]
    draft_model_name = getattr(drafter, "_model", "deepseek")

    # Step 2：DeepSeek 轻量润色（温度低、不重写结构）
    try:
        reviewer = get_provider(req.review_provider, **({"model": req.review_model} if req.review_model else {}))
    except LLMError as exc:
        # 润色失败不阻断整个流程，直接返回初稿
        return DraftResponse(
            title=draft_title,
            body_md=draft_body,
            tags=draft_tags,
            draft_model=draft_model_name,
            review_model=f"(跳过: {exc})",
        )

    review_messages = [
        {"role": "system", "content": _REVIEW_SYSTEM},
        {
            "role": "user",
            "content": (
                f"请润色以下初稿并以 JSON 格式返回。\n"
                f"title: {draft_title}\n"
                f"tags: {draft_tags}\n"
                f"body_md:\n{draft_body}"
            ),
        },
    ]
    try:
        refined = await asyncio.to_thread(reviewer.chat_json, review_messages, temperature=0.4)
        return DraftResponse(
            title=str(refined.get("title", draft_title)),
            body_md=str(refined.get("body_md", draft_body)),
            tags=[str(t) for t in refined.get("tags", draft_tags)],
            draft_model=draft_model_name,
            review_model=getattr(reviewer, "_model", getattr(reviewer, "name", req.review_provider)),
        )
    except Exception:
        # 润色失败降级：返回未润色的初稿
        return DraftResponse(
            title=draft_title,
            body_md=draft_body,
            tags=draft_tags,
            draft_model=draft_model_name,
            review_model="(润色失败，返回初稿)",
        )


# ---------------------- 导出成品包 ----------------------

@app.post("/export")
async def export_zip(req: ExportRequest):
    """把适配结果打包成 ZIP 成品包，每个平台一个 .txt 文件（可直接粘贴发布）。

    这是"诚实版真发布"的最终形态：不假装能发，给用户最干净的成品文件。
    """
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        readme_lines = [
            f"多平台内容成品包",
            f"原标题：{req.title or '（未填）'}",
            "",
            "各平台文件说明：",
        ]
        for result in req.results:
            if result.error:
                continue
            # 优先用 formatted（平台特定格式），否则拼接 title+content
            content_text = result.formatted or f"{result.title}\n\n{result.content}"
            if result.hashtags:
                content_text += "\n\n" + " ".join(f"#{t}" for t in result.hashtags)
            filename = f"{result.display_name}.txt"
            zf.writestr(filename, content_text.encode("utf-8"))
            readme_lines.append(f"  {filename}")
            if result.publish_intent and result.publish_intent.url:
                readme_lines.append(f"    → 发布地址：{result.publish_intent.url}")
        zf.writestr("README.txt", "\n".join(readme_lines).encode("utf-8"))

    zip_bytes = buf.getvalue()
    # Content-Disposition 头只能用 latin-1，中文需用 RFC 5987 的 filename* 参数
    # 为简单起见，用固定英文文件名，避免编码问题
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="multi-publish-export.zip"'},
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


# ---------------------- 历史账户路由 ----------------------

def _row_to_history_item(row: dict) -> HistoryItem:
    """把 database.py 返回的原始 dict 反序列化成 HistoryItem。"""
    import json as _json

    return HistoryItem(
        id=row["id"],
        session_id=row["session_id"],
        title=row["title"],
        body_md=row["body_md"],
        tags=_json.loads(row["tags_json"] or "[]"),
        platforms=_json.loads(row["platforms_json"] or "[]"),
        results=[PlatformResult(**r) for r in _json.loads(row["results_json"] or "[]")],
        created_at=row["created_at"],
    )


@app.get("/history", response_model=HistoryListResponse)
def get_history(session_id: str, limit: int = 20):
    """查询当前 session 的历史记录（最多 limit 条，默认 20）。"""
    if not session_id or len(session_id) > 64:
        raise HTTPException(status_code=400, detail="session_id 非法")
    rows = history_list(session_id, min(limit, 50))
    items = [_row_to_history_item(r) for r in rows]
    return HistoryListResponse(items=items, total=len(items))


@app.post("/history", response_model=HistoryItem)
def save_history(req: SaveHistoryRequest):
    """保存一次适配历史（前端在适配完成后自动调用）。"""
    # 只保存至少有一个成功结果的记录
    success = [r for r in req.results if not r.error]
    if not success:
        raise HTTPException(status_code=400, detail="没有成功的适配结果，不保存")
    row = history_save(
        session_id=req.session_id,
        title=req.title,
        body_md=req.body_md,
        tags=req.tags,
        platforms=req.platforms,
        results=[r.model_dump() for r in req.results],
    )
    return _row_to_history_item(row)


@app.delete("/history/{item_id}")
def delete_history(item_id: int, session_id: str):
    """删除指定历史条目（只能删自己 session 的）。"""
    if not session_id or len(session_id) > 64:
        raise HTTPException(status_code=400, detail="session_id 非法")
    deleted = history_delete(item_id, session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="记录不存在或无权删除")
    return {"ok": True}


def _error_result(name: str, message: str, display_name: str = "") -> PlatformResult:
    """构造一个表示失败的平台结果。"""
    return PlatformResult(
        platform=name,
        display_name=display_name or name,
        title="",
        content="",
        error=message,
    )
