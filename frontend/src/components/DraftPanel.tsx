// AI 起草面板：用户输入主题，DeepSeek 起草初稿，DeepSeek 自审润色，一键载入编辑器。

import { useState } from "react";
import { Loader2, ArrowRight, Sparkles } from "lucide-react";
import { draftContent, type DraftResult } from "../lib/api";

interface Props {
  onUse: (title: string, bodyMd: string, tags: string[]) => void;
}

export default function DraftPanel({ onUse }: Props) {
  const [topic, setTopic] = useState("");
  const [loading, setLoading] = useState(false);
  const [draft, setDraft] = useState<DraftResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleDraft() {
    if (!topic.trim()) {
      setError("请输入文章主题");
      return;
    }
    setError(null);
    setLoading(true);
    setDraft(null);
    try {
      const result = await draftContent(topic.trim());
      setDraft(result);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="rounded-md border border-ink-700 bg-ink-850 p-3.5">
        <div className="mb-2 flex items-center gap-1.5 text-[11px] font-medium tracking-[0.08em] text-paper-faint">
          <Sparkles size={11} />
          AI 起草
        </div>
        <input
          className="w-full bg-transparent text-[14px] text-paper placeholder-paper-faint focus:outline-none"
          placeholder="输入文章主题，例如：远程办公的利与弊"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              handleDraft();
            }
          }}
        />
        <p className="mt-2 text-[11px] text-paper-faint">
          DeepSeek 起草初稿 → DeepSeek 自审润色 → 一键载入编辑器
        </p>
      </div>

      <button
        onClick={handleDraft}
        disabled={loading}
        className="flex items-center justify-center gap-1.5 rounded bg-clay py-2.5 text-[14px] font-semibold text-white transition-colors hover:bg-clay-hover disabled:opacity-60"
      >
        {loading && <Loader2 size={15} className="animate-spin" />}
        {loading ? "生成中…" : (
          <>
            AI 帮我起草
            <ArrowRight size={15} />
          </>
        )}
      </button>

      {error && (
        <div className="rounded border border-red-900/60 bg-red-950/40 px-3 py-2 text-sm text-red-300">
          {error}
        </div>
      )}

      {draft && (
        <div className="rounded-md border border-ink-700 bg-ink-850 p-3.5">
          <p className="text-[13px] font-semibold text-paper">{draft.title}</p>
          <p className="mt-1 text-[11px] text-paper-faint">
            起草：{draft.draft_model} · 润色：{draft.review_model}
          </p>
          <p className="mt-2 line-clamp-4 text-[12px] leading-relaxed text-paper-dim">
            {draft.body_md.replace(/[#*`>[\]]/g, "").slice(0, 200)}
          </p>
          <button
            onClick={() => onUse(draft.title, draft.body_md, draft.tags)}
            className="mt-3 flex items-center gap-1 rounded border border-clay px-3 py-1.5 text-[13px] font-medium text-clay transition-colors hover:bg-clay-soft"
          >
            用这篇
            <ArrowRight size={13} />
          </button>
        </div>
      )}
    </div>
  );
}
