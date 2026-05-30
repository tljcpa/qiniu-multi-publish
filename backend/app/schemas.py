"""API 请求 / 响应模型。"""

from __future__ import annotations

from pydantic import BaseModel, Field

from adapters.base import ContentInput


class AdaptRequest(BaseModel):
    """POST /adapt 请求体。"""

    content: ContentInput = Field(..., description="用户原始内容")
    # 目标平台 name 列表；为空表示适配到所有已注册平台
    platforms: list[str] = Field(default_factory=list, description="目标平台，空=全部")
    # LLM 后端，默认 deepseek；可传 azure 做多模型对比
    provider: str = Field(default="deepseek", description="LLM 后端")
    # 可选指定具体模型（如 deepseek-reasoner），为空用后端默认
    model: str | None = Field(default=None, description="具体模型名，可选")


class PublishIntent(BaseModel):
    """一键发布意图：复制内容 + 跳转 URL（不替用户发布）。"""

    clipboard: str
    url: str


class PlatformInfo(BaseModel):
    """平台元信息（GET /platforms）。"""

    name: str
    display_name: str
    editor_url: str
    preview_template: str
    extension_guide: str = ""


class PlatformResult(BaseModel):
    """单个平台的适配结果（POST /adapt 的元素）。"""

    platform: str
    display_name: str
    title: str
    content: str
    summary: str = ""
    hashtags: list[str] = Field(default_factory=list)
    model: str = ""
    preview_template: str = "generic"
    # 渲染好的、可直接粘贴的文本
    formatted: str = ""
    publish_intent: PublishIntent | None = None
    # 该平台适配失败时填错误信息，成功为 None（部分失败不影响其它平台）
    error: str | None = None


class AdaptResponse(BaseModel):
    """POST /adapt 响应体。"""

    results: list[PlatformResult]


# ---------------------- 多模型对比（亮点6） ----------------------
class ModelOption(BaseModel):
    """一个可用的 LLM 模型选项（GET /models）。"""

    label: str          # 显示名，如 "DeepSeek Chat"
    provider: str       # "deepseek" | "azure"
    model: str          # 具体模型/部署名


class CompareVariant(BaseModel):
    """对比请求里的一个模型变体。"""

    label: str
    provider: str
    model: str | None = None


class CompareRequest(BaseModel):
    """POST /compare 请求体：单平台、多模型对比。"""

    content: ContentInput
    platform: str
    variants: list[CompareVariant] = Field(default_factory=list, description="参与对比的模型，空=用默认两个")


class CompareVariantResult(BaseModel):
    """单个模型变体在该平台的适配结果 + 耗时。"""

    label: str
    provider: str
    model: str
    latency_ms: int = 0
    result: PlatformResult


class CompareResponse(BaseModel):
    """POST /compare 响应体。"""

    platform: str
    display_name: str
    variants: list[CompareVariantResult]


# ---------------------- 发布策略 Agent（创新） ----------------------
class StrategyRequest(BaseModel):
    """POST /strategy 请求体。"""

    content: ContentInput
    provider: str = "deepseek"
    model: str | None = None


class PlatformScore(BaseModel):
    platform: str
    display_name: str
    score: int          # 0-100 契合度
    reason: str
    recommended: bool


class StrategyResponse(BaseModel):
    scores: list[PlatformScore]


class IdeasRequest(BaseModel):
    """POST /ideas 请求体：为单个平台生成创意。"""

    content: ContentInput
    platform: str
    provider: str = "deepseek"
    model: str | None = None


class IdeasResponse(BaseModel):
    platform: str
    display_name: str
    titles: list[str]
    hashtags: list[str]
    cover_copy: list[str]
    model: str = ""
    error: str | None = None


# ---------------------- 历史账户 ----------------------

class HistoryItem(BaseModel):
    """单条历史记录（对应 history 表一行）。"""

    id: int
    session_id: str
    title: str
    body_md: str
    tags: list[str]
    platforms: list[str]
    results: list[PlatformResult]
    created_at: str


class SaveHistoryRequest(BaseModel):
    """POST /history 请求体。"""

    session_id: str = Field(..., min_length=1, max_length=64, description="客户端匿名 UUID")
    title: str = ""
    body_md: str = ""
    tags: list[str] = Field(default_factory=list)
    platforms: list[str] = Field(default_factory=list)
    results: list[PlatformResult] = Field(default_factory=list)


class HistoryListResponse(BaseModel):
    items: list[HistoryItem]
    total: int
