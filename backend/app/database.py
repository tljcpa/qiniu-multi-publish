"""SQLite 数据库初始化与基础查询。

使用 Python 内置 sqlite3，不引入额外 ORM 依赖，轻量够用。
数据库文件路径从环境变量 DB_PATH 读取（默认 /data/multi_publish.db），
对应 docker-compose.yml 里 backend_data volume 的挂载点。
"""

from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path

DB_PATH = Path(os.getenv("DB_PATH", "/data/multi_publish.db"))
# 每个 session 最多保留 50 条历史，防止无限增长
_HISTORY_LIMIT = 50


def _open() -> sqlite3.Connection:
    """打开 SQLite 连接，WAL 模式减少写阻塞。"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """建表 + 索引（幂等，首次启动时调用）。"""
    with _open() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id     TEXT    NOT NULL,
                title          TEXT    NOT NULL DEFAULT '',
                body_md        TEXT    NOT NULL DEFAULT '',
                tags_json      TEXT    NOT NULL DEFAULT '[]',
                platforms_json TEXT    NOT NULL DEFAULT '[]',
                results_json   TEXT    NOT NULL DEFAULT '[]',
                created_at     TEXT    NOT NULL
                    DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_hist_session
            ON history(session_id, id DESC)
        """)


def history_list(session_id: str, limit: int = 20) -> list[dict]:
    """返回该 session 最近 limit 条历史，按时间倒序。"""
    with _open() as conn:
        rows = conn.execute(
            "SELECT * FROM history WHERE session_id = ? ORDER BY id DESC LIMIT ?",
            (session_id, limit),
        ).fetchall()
    return [dict(r) for r in rows]


def history_save(
    session_id: str,
    title: str,
    body_md: str,
    tags: list,
    platforms: list,
    results: list,
) -> dict:
    """插入一条历史，并修剪超出限额的旧记录，返回新插入行。"""
    with _open() as conn:
        cur = conn.execute(
            """INSERT INTO history
               (session_id, title, body_md, tags_json, platforms_json, results_json)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                session_id,
                title,
                body_md,
                json.dumps(tags, ensure_ascii=False),
                json.dumps(platforms, ensure_ascii=False),
                json.dumps(results, ensure_ascii=False),
            ),
        )
        new_id = cur.lastrowid
        # 修剪：保留最新 _HISTORY_LIMIT 条，按 id 倒序
        conn.execute(
            """DELETE FROM history WHERE session_id = ? AND id NOT IN (
               SELECT id FROM history WHERE session_id = ? ORDER BY id DESC LIMIT ?)""",
            (session_id, session_id, _HISTORY_LIMIT),
        )

    with _open() as conn:
        row = conn.execute(
            "SELECT * FROM history WHERE id = ?", (new_id,)
        ).fetchone()
    return dict(row)


def history_delete(item_id: int, session_id: str) -> bool:
    """删除指定条目（只能删自己 session 的）。返回是否实际删除了。"""
    with _open() as conn:
        cur = conn.execute(
            "DELETE FROM history WHERE id = ? AND session_id = ?",
            (item_id, session_id),
        )
    return cur.rowcount > 0
