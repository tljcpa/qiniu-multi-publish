"""小红书平台适配器。

风格定位（见 docs/复盘.md D-05）：emoji 密集、数字/痛点标题、'姐妹们/宝子们'、短句、话题标签多。
本 adapter 覆写了 output_schema 与 format_content，体现'每个平台可按需扩展'。
"""

from __future__ import annotations

from adapters.base import AdaptedResult, PlatformAdapter, register


@register
class XhsAdapter(PlatformAdapter):
    """小红书（XHS）适配器。"""

    name = "xhs"
    display_name = "小红书"
    # 跳转到小红书创作服务平台发布页（D-01：只跳转，不替用户发布）
    editor_url = "https://creator.xiaohongshu.com/publish/publish?source=official"

    def style_prompt(self) -> str:
        return (
            "你是小红书爆款博主，擅长把内容改写成小红书种草笔记的风格。\n"
            "请严格遵循小红书的风格规则：\n"
            "1. 语气：亲切、有感染力，多用'姐妹们''宝子们''集美们'，像在跟好朋友安利。\n"
            "2. 标题：必须抓眼球！用 emoji + 数字 + 痛点/利益点，如'❌别再踩坑了！3 个方法亲测有效✅'，控制在 20 字内。\n"
            "3. 开头：先戳痛点或制造共鸣，'是不是总觉得……''我之前也一样……'。\n"
            "4. 段落：超短句，多换行，几乎每句都可带 emoji，营造轻松刷帖感。\n"
            "5. 排版：可用 emoji 当小标题项目符号（如 ✨📌💡），分点清晰。\n"
            "6. 结尾：引导互动，'码住别丢啦📌''有用记得点赞收藏💕''评论区扣 1'。\n"
            "7. 话题标签：生成 5-8 个相关话题标签放进 hashtags（不带 # 号）。\n"
            "保持原文事实与观点，只改写风格，emoji 要自然别堆到辣眼睛。"
        )

    def output_schema(self) -> dict:
        # 小红书强依赖话题标签与封面文案，扩展默认 schema
        schema = super().output_schema()
        schema["title"] = "带 emoji + 数字/痛点的爆款标题（20 字内）"
        schema["hashtags"] = "5-8 个话题标签字符串数组（不含 # 号）"
        schema["cover_alt"] = "建议的封面图文案（一句话，可选）"
        return schema

    def format_content(self, adapted: AdaptedResult) -> str:
        # 小红书笔记：标题在最上，正文后跟一排 #话题，符合粘贴习惯
        parts = [adapted.title, "", adapted.content]
        if adapted.hashtags:
            parts.append("")
            parts.append(" ".join("#" + tag for tag in adapted.hashtags))
        return "\n".join(parts)

    def extension_guide(self) -> str:
        return (
            "小红书坑位：① 正文不支持富文本/Markdown，只能纯文本 + emoji，标题与正文分开输入；"
            "② 笔记需至少 1 张图才能发布，本工具只产出文案，图片需手动；"
            "③ 话题标签放正文末尾，过多(>10)会被限流。"
        )
