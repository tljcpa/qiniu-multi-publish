"""公众号（微信公众号）平台适配器。

风格定位（见 docs/复盘.md D-05）：正式商务、段落短、有引言/结语、emoji 克制、标题有冲击力。
风格知识写在 style_prompt 里（我们自己总结的规则，不抄真实内容，见 D-06）。
"""

from __future__ import annotations

from adapters.base import PlatformAdapter, register


@register
class WeChatAdapter(PlatformAdapter):
    """微信公众号适配器。"""

    name = "wechat"
    display_name = "公众号"
    # 公众号没有公开发布 API，跳转到官方后台首页，由用户登录后新建图文（D-01）
    editor_url = "https://mp.weixin.qq.com/"

    def style_prompt(self) -> str:
        return (
            "你是资深的微信公众号主编，擅长把内容改写成公众号爆款图文的风格。\n"
            "请严格遵循公众号的风格规则：\n"
            "1. 语气：正式但不死板，专业、有温度，面向认真阅读的读者。\n"
            "2. 标题：要有冲击力和价值感，可用'为什么/如何/这一点'等句式，控制在 22 字内，不堆 emoji。\n"
            "3. 段落：短段落，每段 2-4 句，多用小标题分节，方便手机竖屏阅读。\n"
            "4. 结构：开头有一段引言钩住读者，中间分点论述，结尾有总结或行动号召。\n"
            "5. emoji：克制使用，全文不超过 3 个，且只在小标题或关键处点缀。\n"
            "6. 互动：结尾可加一句温和的引导，如'点个在看，我们下篇见'。\n"
            "保持原文的事实与观点，只改写表达风格，不要编造数据。"
        )

    def output_schema(self) -> dict:
        # 在通用 schema 上补充公众号关心的"引导语"
        schema = super().output_schema()
        schema["summary"] = "开头引言（一段，钩住读者）"
        return schema

    def strategy_profile(self) -> dict:
        return {
            "content_types": ["深度长文", "行业观点", "教程攻略", "品牌叙事"],
            "ideal_length": "中长（800-2500 字）",
            "tone": "正式、专业、有体系",
            "note": "适合有完整论述结构的深度内容；纯碎片化/强视觉的内容不占优势。",
        }

    def extension_guide(self) -> str:
        return (
            "公众号坑位：① 正文图片需先上传素材库，本工具只产出文本，图片需手动；"
            "② 公众号正文支持有限 HTML（部分标签被过滤），建议粘贴富文本而非源码；"
            "③ 单篇标题上限 64 字，但实操 22 字内点击率更好。"
        )
