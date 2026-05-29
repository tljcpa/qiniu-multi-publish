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
