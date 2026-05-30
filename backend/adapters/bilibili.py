"""B 站（哔哩哔哩）专栏适配器。

风格定位（见 docs/复盘.md D-05）：口语化、活泼、'家人们/UP 主'、结尾求'三连'、轻松互动。
"""

from __future__ import annotations

from adapters.base import PlatformAdapter, register


@register
class BilibiliAdapter(PlatformAdapter):
    """B 站专栏适配器。"""

    name = "bilibili"
    display_name = "B站"
    # 跳转到 B 站专栏编辑器（D-01：只跳转，不替用户发布）
    editor_url = "https://member.bilibili.com/read/editor/"

    def style_prompt(self) -> str:
        return (
            "你是 B 站知名 UP 主，擅长把内容改写成 B 站专栏的风格。\n"
            "请严格遵循 B 站的风格规则：\n"
            "1. 语气：轻松、口语化、有网感，像在跟粉丝唠嗑，可适度用'家人们''兄弟们''UP 主'自称。\n"
            "2. 标题：活泼带点夸张和好奇心，可用'我愿称之为''血赚''看完直接破防'等网络梗（适度）。\n"
            "3. 段落：短句多、节奏快，可用 emoji 点缀活跃气氛，但别铺满。\n"
            "4. 结构：开头先抛一个吸引人的钩子或共鸣点，中间口语化讲解，穿插一点玩梗。\n"
            "5. 互动：结尾必须有互动引导，如'觉得有用的话，点赞投币收藏一键三连支持一下！''评论区聊聊你的看法'。\n"
            "保持原文的事实与观点，只改写表达风格，玩梗适度别喧宾夺主。"
        )

    def strategy_profile(self) -> dict:
        return {
            "content_types": ["教程", "测评", "科普", "娱乐向", "盘点"],
            "ideal_length": "中短（轻松好读）",
            "tone": "口语、活泼、有网感有梗",
            "note": "适合年轻向、可玩梗的内容；过于严肃刻板的长篇不占优势。",
        }

    def extension_guide(self) -> str:
        return (
            "B 站坑位：① 专栏对 Markdown 支持有限，建议粘贴纯文本/富文本后用编辑器排版；"
            "② emoji 在专栏正常显示但过量会被判营销；"
            "③ 标题 40 字内，含梗但别太标题党，否则限流。"
        )
