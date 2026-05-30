"""Platform Adapter 插件化架构核心。

本模块定义：
- ContentInput：用户原始内容的统一模型（所有平台共享的输入）。
- AdaptedResult：适配后结果的统一模型。
- PlatformAdapter：所有平台 adapter 的抽象基类（模板方法模式）。
- register / get_adapter / all_adapters：平台注册表。

设计目标（见 docs/复盘.md D-04）：新增一个平台 = 写一个子类 + @register，约 100 行。
真正必须实现的只有"身份 + 风格"，其余方法都有可复用的默认实现。
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod

from pydantic import BaseModel, Field

from app.llm_provider import LLMProvider


class ContentInput(BaseModel):
    """用户输入的原始内容（平台无关）。"""

    title: str = Field(..., description="原始标题")
    body_md: str = Field(..., description="正文，Markdown 格式")
    tags: list[str] = Field(default_factory=list, description="作者给的标签 / 关键词")


class AdaptedResult(BaseModel):
    """单个平台的适配结果（结构化）。

    这是 LLM 结构化输出 + adapter 渲染后的统一产物，前端据此预览/复制/跳转。
    """

    platform: str = Field(..., description="平台 name")
    title: str = Field(..., description="适配后的标题")
    content: str = Field(..., description="适配后的正文（已是该平台风格的文本/markdown）")
    summary: str = Field(default="", description="摘要 / 导语")
    hashtags: list[str] = Field(default_factory=list, description="话题标签")
    model: str = Field(default="", description="使用的 LLM 后端，用于多模型对比标注")


class PlatformIdeas(BaseModel):
    """发布策略 Agent 为某平台生成的创意点子（标题/标签/封面文案）。"""

    platform: str
    titles: list[str] = Field(default_factory=list, description="符合本平台风格的标题候选")
    hashtags: list[str] = Field(default_factory=list, description="本平台话题标签（不含 #）")
    cover_copy: list[str] = Field(default_factory=list, description="封面/首图文案建议")
    model: str = Field(default="")


def _coerce_list(value) -> list[str]:
    """把 LLM 可能返回的字符串/列表统一成字符串列表。"""
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str):
        return [s.strip().lstrip("#") for s in value.replace("，", ",").split(",") if s.strip()]
    return []


# ---------------------------------------------------------------------------
# 抽象基类
# ---------------------------------------------------------------------------
class PlatformAdapter(ABC):
    """平台适配器抽象基类。

    必须实现（每个平台必然不同）：
        name / display_name / editor_url 三个类属性 + style_prompt()
    可选覆写（有可复用默认实现）：
        few_shot / output_schema / format_content / preview_template /
        publish_intent / extension_guide
    """

    # --- 必须由子类提供的身份信息 ---
    name: str = ""           # 平台唯一标识，如 "wechat"
    display_name: str = ""   # 中文显示名，如 "公众号"
    editor_url: str = ""     # 平台官方"写新内容"入口 URL（跳转目标）

    # ---------------------- 必须实现的抽象方法 ----------------------
    @abstractmethod
    def style_prompt(self) -> str:
        """返回该平台的风格适配系统提示词。

        描述该平台的语气、段落结构、互动话术、标题习惯等。这是风格适配的灵魂。
        """
        raise NotImplementedError

    # ---------------------- 可选覆写的方法（带默认实现） ----------------------
    def few_shot(self) -> list[dict]:
        """少量风格样本（few-shot），默认空。

        返回形如 [{"role": "user", ...}, {"role": "assistant", ...}] 的消息对。
        仅用于 prompt 内风格学习，样本内容不入 git（版权，见 D-06）。
        """
        return []

    def output_schema(self) -> dict:
        """LLM 结构化输出的期望字段说明（用于 prompt 指导）。

        默认通用 schema；特殊平台（如需要 cover_alt）可覆写追加字段。
        """
        return {
            "title": "适配后的标题（符合本平台标题习惯）",
            "content": "适配后的正文（本平台风格）",
            "summary": "一句话摘要 / 导语",
            "hashtags": "话题标签字符串数组",
        }

    def format_content(self, adapted: AdaptedResult) -> str:
        """把适配结果渲染成可粘贴的文本/HTML，默认拼接标题+正文+标签。

        平台若有特殊排版（如小红书 emoji 包裹标题）可覆写。
        """
        parts = [adapted.title, "", adapted.content]
        if adapted.hashtags:
            parts.append("")
            parts.append(" ".join("#" + tag for tag in adapted.hashtags))
        return "\n".join(parts)

    def preview_template(self) -> str:
        """返回该平台预览外观的标识，默认 "generic"。

        前端按这个标识选用对应的 CSS 仿真模板（PR12）。
        """
        return "generic"

    def publish_intent(self, adapted: AdaptedResult) -> dict:
        """返回前端"一键发布"所需的意图：复制内容 + 跳转 URL。

        体现产品定位（D-01）：我们只复制 + 跳转，不替用户发布。
        """
        return {
            "clipboard": self.format_content(adapted),
            "url": self.editor_url,
        }

    def extension_guide(self) -> str:
        """该平台开发注意事项（字符限制、标签支持等），默认空。"""
        return ""

    # ---------------------- 发布策略：平台定位档案 + 创意生成 ----------------------
    def strategy_profile(self) -> dict:
        """该平台适合什么内容（供发布策略 Agent 打分判断该不该发）。

        默认通用档案；每个平台覆写以描述自己的内容类型 / 长度甜区 / 调性。
        新平台只要填这个档案，就能自动进入"该发哪些平台"的打分，无需改 Agent。
        """
        return {
            "content_types": ["通用图文"],
            "ideal_length": "中等",
            "tone": "中性",
            "note": "",
        }

    def ideas_schema(self) -> dict:
        """创意生成的 JSON 输出说明（标题/标签/封面文案），子类可覆写补字段。"""
        return {
            "titles": "3 个符合本平台风格的标题候选（字符串数组）",
            "hashtags": "5-8 个本平台话题标签，不带 # 号（字符串数组）",
            "cover_copy": "1-2 条封面/首图文案建议（字符串数组）",
        }

    def generate_ideas(self, content: ContentInput, provider: LLMProvider, *,
                       temperature: float = 0.8) -> PlatformIdeas:
        """为本平台生成原生标题/话题标签/封面文案建议（不改写正文）。

        复用 style_prompt 保证创意符合平台调性；temperature 略高以增创意多样性。
        """
        messages: list[dict] = [{
            "role": "system",
            "content": self.style_prompt() + "\n\n你现在只产出发布创意（标题、话题标签、封面文案），不要改写或输出正文。",
        }]
        messages.append({"role": "user", "content": self._build_ideas_prompt(content)})
        raw = provider.chat_json(messages, temperature=temperature)
        return PlatformIdeas(
            platform=self.name,
            titles=_coerce_list(raw.get("titles")),
            hashtags=_coerce_list(raw.get("hashtags")),
            cover_copy=_coerce_list(raw.get("cover_copy")),
            model=getattr(provider, "name", ""),
        )

    def _build_ideas_prompt(self, content: ContentInput) -> str:
        schema_desc = json.dumps(self.ideas_schema(), ensure_ascii=False, indent=2)
        tag_line = "、".join(content.tags) or "（无）"
        return (
            f"根据下面这篇内容，为本平台生成发布创意。\n\n"
            f"原标题：{content.title}\n"
            f"作者标签：{tag_line}\n"
            f"原正文（节选）：\n{content.body_md[:1200]}\n\n"
            f"只输出一个 JSON 对象，字段含义如下：\n{schema_desc}"
        )

    # ---------------------- 模板方法（编排，基类统一实现） ----------------------
    def adapt(self, content: ContentInput, provider: LLMProvider, *,
              temperature: float = 0.7) -> AdaptedResult:
        """把原始内容适配为本平台风格（核心编排，子类一般不覆写）。

        流程：system(style_prompt) + few_shot 样本 + user(原文 + schema 要求)
              -> provider.chat_json -> 组装 AdaptedResult。
        """
        messages: list[dict] = [{"role": "system", "content": self.style_prompt()}]
        messages.extend(self.few_shot())
        messages.append({"role": "user", "content": self._build_user_prompt(content)})

        raw = provider.chat_json(messages, temperature=temperature)
        return self._to_result(raw, provider)

    def _build_user_prompt(self, content: ContentInput) -> str:
        """组装用户消息：原文 + 标签 + 要求按 JSON schema 输出。"""
        schema_desc = json.dumps(self.output_schema(), ensure_ascii=False, indent=2)
        tag_line = "、".join(content.tags)
        if not tag_line:
            tag_line = "（无）"
        return (
            f"请把下面这篇内容适配为本平台风格。\n\n"
            f"原标题：{content.title}\n"
            f"作者标签：{tag_line}\n"
            f"原正文（Markdown）：\n{content.body_md}\n\n"
            f"只输出一个 JSON 对象，字段含义如下：\n{schema_desc}"
        )

    def _to_result(self, raw: dict, provider: LLMProvider) -> AdaptedResult:
        """把 LLM 返回的 dict 收敛成 AdaptedResult，容忍缺字段。"""
        hashtags = raw.get("hashtags", [])
        # LLM 偶尔把 hashtags 返回成字符串，做一次兜底归一
        if isinstance(hashtags, str):
            hashtags = [t.strip().lstrip("#") for t in hashtags.replace("，", ",").split(",") if t.strip()]
        return AdaptedResult(
            platform=self.name,
            title=raw.get("title", ""),
            content=raw.get("content", ""),
            summary=raw.get("summary", ""),
            hashtags=hashtags,
            model=getattr(provider, "name", ""),
        )


# ---------------------------------------------------------------------------
# 平台注册表
# ---------------------------------------------------------------------------
# 全局注册表：name -> adapter 实例
_REGISTRY: dict[str, PlatformAdapter] = {}


def register(cls: type[PlatformAdapter]) -> type[PlatformAdapter]:
    """类装饰器：把一个 PlatformAdapter 子类注册进全局注册表。

    用法：
        @register
        class MyAdapter(PlatformAdapter):
            name = "my-platform"
            ...
    """
    if not getattr(cls, "name", ""):
        raise ValueError(f"{cls.__name__} 必须设置非空的 name 类属性才能注册")
    instance = cls()
    if instance.name in _REGISTRY:
        raise ValueError(f"平台 name 重复注册: {instance.name}")
    _REGISTRY[instance.name] = instance
    return cls


def get_adapter(name: str) -> PlatformAdapter:
    """按 name 取 adapter 实例，不存在则报错。"""
    if name not in _REGISTRY:
        raise KeyError(f"未注册的平台: {name}（已注册: {list(_REGISTRY)}）")
    return _REGISTRY[name]


def all_adapters() -> list[PlatformAdapter]:
    """返回所有已注册的 adapter 实例。"""
    return list(_REGISTRY.values())


def platform_names() -> list[str]:
    """返回所有已注册平台的 name 列表。"""
    return list(_REGISTRY)
