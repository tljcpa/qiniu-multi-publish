"""流式适配辅助：构造流式 prompt + 解析流式纯文本结果。

流式端点不走 JSON mode（增量 JSON 不可解析），改用纯文本约定格式：
    第一行：标题
    （空行）
    正文（可用 Markdown）
    最后一行：TAGS: 标签1, 标签2, ...
边流边显原始文本（打字机），结束后用 parse_streamed 还原成结构化结果。
见 docs/复盘.md D-15。
"""

from __future__ import annotations

import re

from adapters.base import AdaptedResult, ContentInput, PlatformAdapter

# 流式输出格式说明（追加到 user 消息）
_STREAM_FORMAT = (
    "请把下面内容适配为本平台风格，并严格按如下纯文本格式输出"
    "（不要使用 ``` 代码块，不要输出 JSON）：\n"
    "第一行：标题\n"
    "第二行：留空\n"
    "接下来若干行：正文（可用 Markdown）\n"
    "最后另起一行：以 TAGS: 开头，列出话题标签，用逗号分隔；若无标签就只写 TAGS:\n"
)


def build_stream_messages(adapter: PlatformAdapter, content: ContentInput) -> list[dict]:
    """构造流式适配的消息：复用平台 style_prompt 与 few-shot，仅换输出格式说明。"""
    tag_line = "、".join(content.tags)
    if not tag_line:
        tag_line = "（无）"
    user = (
        f"{_STREAM_FORMAT}\n"
        f"原标题：{content.title}\n"
        f"作者标签：{tag_line}\n"
        f"原正文（Markdown）：\n{content.body_md}"
    )
    messages: list[dict] = [{"role": "system", "content": adapter.style_prompt()}]
    messages.extend(adapter.few_shot())
    messages.append({"role": "user", "content": user})
    return messages


def parse_streamed(platform: str, text: str, model: str) -> AdaptedResult:
    """把流式纯文本结果还原成 AdaptedResult（容错解析）。"""
    lines = text.splitlines()

    # 跳过开头空行，第一非空行作为标题
    idx = 0
    while idx < len(lines) and not lines[idx].strip():
        idx += 1
    title = ""
    if idx < len(lines):
        title = lines[idx].strip()
        idx += 1

    tags: list[str] = []
    body_lines: list[str] = []
    for line in lines[idx:]:
        stripped = line.strip()
        if stripped.startswith("TAGS:") or stripped.startswith("TAGS："):
            # 取冒号后的标签串，中英文冒号都兼容
            tag_str = re.split(r"[:：]", stripped, maxsplit=1)[1] if re.search(r"[:：]", stripped) else ""
            tags = [t.strip().lstrip("#") for t in re.split(r"[,，]", tag_str) if t.strip()]
        else:
            body_lines.append(line)

    content_body = "\n".join(body_lines).strip()
    return AdaptedResult(
        platform=platform,
        title=title,
        content=content_body,
        summary="",
        hashtags=tags,
        model=model,
    )
