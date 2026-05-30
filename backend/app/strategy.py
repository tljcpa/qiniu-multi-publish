"""发布策略 Agent：判断一段内容该发哪些平台。

做法：收集所有已注册平台的 strategy_profile（定位档案），连同用户内容，
让 LLM 一次性给每个平台打契合度分 + 理由 + 是否推荐。
平台档案随 Adapter 走——新增平台只要在其 Adapter 写 strategy_profile，
就自动进入打分，无需改本 Agent（呼应题目"扩展架构"加分点）。
"""

from __future__ import annotations

import json

from adapters.base import ContentInput, PlatformAdapter
from app.llm_provider import LLMProvider

# 推荐阈值：分数 >= 此值视为推荐发布
RECOMMEND_THRESHOLD = 60


def recommend_platforms(
    content: ContentInput,
    provider: LLMProvider,
    adapters: list[PlatformAdapter],
    *,
    temperature: float = 0.4,
) -> list[dict]:
    """为每个平台返回 {platform, display_name, score, reason, recommended}。"""
    # 组装各平台定位档案
    profiles = [
        {"platform": a.name, "display_name": a.display_name, "profile": a.strategy_profile()}
        for a in adapters
    ]
    name_map = {a.name: a.display_name for a in adapters}

    tag_line = "、".join(content.tags) or "（无）"
    system = (
        "你是资深的社交媒体发布策略顾问。根据一段内容的题材、长度、调性，"
        "判断它适合发到哪些平台。要诚实：不合适的平台就给低分，不要每个都推荐。"
    )
    user = (
        f"内容标题：{content.title}\n"
        f"作者标签：{tag_line}\n"
        f"正文（节选）：\n{content.body_md[:1500]}\n\n"
        f"下面是各平台的定位档案（JSON）：\n"
        f"{json.dumps(profiles, ensure_ascii=False, indent=2)}\n\n"
        f"请为每个平台打一个 0-100 的契合度分，并给一句不超过 30 字的理由。"
        f"分数越高表示越适合发到该平台。\n"
        f"只输出 JSON：{{\"scores\":[{{\"platform\":\"wechat\",\"score\":78,\"reason\":\"...\"}}, ...]}}"
    )

    raw = provider.chat_json(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=temperature,
    )

    scored = raw.get("scores", [])
    results: list[dict] = []
    seen = set()
    for item in scored:
        name = item.get("platform")
        if name not in name_map or name in seen:
            continue
        seen.add(name)
        score = _clamp_score(item.get("score"))
        results.append({
            "platform": name,
            "display_name": name_map[name],
            "score": score,
            "reason": str(item.get("reason", "")).strip(),
            "recommended": score >= RECOMMEND_THRESHOLD,
        })

    # LLM 漏掉的平台兜底补上（中性分，不推荐），保证每个平台都有结果
    for a in adapters:
        if a.name not in seen:
            results.append({
                "platform": a.name,
                "display_name": a.display_name,
                "score": 0,
                "reason": "模型未返回该平台评分",
                "recommended": False,
            })

    # 按分数降序，便于前端展示"最该发"在前
    results.sort(key=lambda r: r["score"], reverse=True)
    return results


def _clamp_score(value) -> int:
    """把分数收敛到 0-100 的整数，容忍非法输入。"""
    try:
        score = int(round(float(value)))
    except (TypeError, ValueError):
        return 0
    return max(0, min(100, score))
