// 历史记录侧边板：展示当前 session 的历史适配记录，支持点击恢复、删除。

import { useState, useEffect } from "react";
import { X, Clock, RotateCcw, Trash2 } from "lucide-react";
import { fetchHistory, deleteHistory, type HistoryItem } from "../lib/api";

interface Props {
  sessionId: string;
  onRestore: (item: HistoryItem) => void;
  onClose: () => void;
}

export default function HistoryPanel({ sessionId, onRestore, onClose }: Props) {
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchHistory(sessionId)
      .then(setItems)
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }, [sessionId]);

  async function handleDelete(id: number) {
    await deleteHistory(id, sessionId).catch(() => {});
    setItems((prev) => prev.filter((i) => i.id !== id));
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-end bg-ink-950/70 backdrop-blur-sm"
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <aside className="h-full w-full max-w-sm overflow-y-auto border-l border-ink-700 bg-ink-900 p-5 shadow-2xl">
        <div className="mb-4 flex items-center justify-between">
          <div className="flex items-center gap-2 text-paper">
            <Clock size={14} className="text-paper-faint" />
            <span className="font-serif text-[16px] font-semibold">历史记录</span>
          </div>
          <button onClick={onClose} className="text-paper-faint transition-colors hover:text-paper">
            <X size={18} />
          </button>
        </div>

        {loading && (
          <p className="text-[13px] text-paper-faint">加载中…</p>
        )}
        {!loading && items.length === 0 && (
          <p className="text-[13px] leading-relaxed text-paper-faint">
            暂无历史记录。适配成功后自动保存，最多保留 50 条。
          </p>
        )}

        <ul className="flex flex-col gap-3">
          {items.map((item) => (
            <li key={item.id} className="rounded-md border border-ink-700 bg-ink-850 p-3">
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0 flex-1">
                  <p className="truncate text-[13px] font-medium text-paper">
                    {item.title || "(无标题)"}
                  </p>
                  <p className="mt-0.5 font-mono text-[11px] text-paper-faint">
                    {item.platforms.join(" / ")} · {item.created_at.slice(0, 16).replace("T", " ")}
                  </p>
                </div>
                <div className="flex shrink-0 items-center gap-1">
                  <button
                    onClick={() => { onRestore(item); onClose(); }}
                    className="rounded p-1 text-paper-dim transition-colors hover:text-paper"
                    title="恢复到编辑器"
                  >
                    <RotateCcw size={13} />
                  </button>
                  <button
                    onClick={() => handleDelete(item.id)}
                    className="rounded p-1 text-paper-dim transition-colors hover:text-red-400"
                    title="删除"
                  >
                    <Trash2 size={13} />
                  </button>
                </div>
              </div>
              {item.body_md && (
                <p className="mt-2 line-clamp-2 text-[12px] leading-relaxed text-paper-faint">
                  {item.body_md.replace(/[#*`>[\]]/g, "").slice(0, 120)}
                </p>
              )}
            </li>
          ))}
        </ul>
      </aside>
    </div>
  );
}
