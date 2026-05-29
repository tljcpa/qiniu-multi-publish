"""知乎平台适配器。

风格定位（见 docs/复盘.md D-05）：严谨、长段落、数据/逻辑论证、引用、克制理性的'答主'语气。
"""

from __future__ import annotations

from adapters.base import PlatformAdapter, register


@register
class ZhihuAdapter(PlatformAdapter):
    """知乎专栏 / 回答适配器。"""

    name = "zhihu"
    display_name = "知乎"
    # 跳转到知乎专栏写文章页（D-01：只跳转，不替用户发布）
    editor_url = "https://zhuanlan.zhihu.com/write"

    def style_prompt(self) -> str:
        return (
            "你是知乎高赞答主，擅长把内容改写成知乎专栏/回答的风格。\n"
            "请严格遵循知乎的风格规则：\n"
            "1. 语气：理性、严谨、有信息密度，像在认真解答一个问题，避免浮夸和营销腔。\n"
            "2. 标题：偏好疑问句或'如何看待/为什么/……是一种怎样的体验'句式，引发思考。\n"
            "3. 段落：可以用较长段落充分论证，先抛观点再展开论据，逻辑层层递进。\n"
            "4. 论证：尽量给出原因、机制、对比或条件，体现'讲清楚为什么'，但不要编造具体数字。\n"
            "5. 结构：开头先给结论或核心判断（先说人话），再分点深入，必要时用'先下结论：'。\n"
            "6. 互动：结尾可加一句'以上，供参考'或'欢迎在评论区补充'，克制不谄媚。\n"
            "保持原文事实与观点，只改写表达风格，不编造数据或引用。"
        )

    def extension_guide(self) -> str:
        return (
            "知乎坑位：① 知乎正文支持 Markdown 但公式/代码块渲染有差异；"
            "② 外链会被降权，引用尽量用文字描述来源；"
            "③ 标题党会被折叠，疑问句式比夸张陈述更安全。"
        )
