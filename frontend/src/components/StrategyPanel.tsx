// 发布策略面板：各平台契合度排行（分数条 + 理由 + 推荐），按需为平台生成原生创意。
import { useState, type ReactNode } from "react";
import { Copy, Check, Loader2 } from "lucide-react";
import type { IdeasResult, PlatformScore } from "../lib/api";
import { copyText } from "../lib/clipboard";

type IdeasState = IdeasResult | "loading" | undefined;

interface StrategyPanelProps {
  scores: PlatformScore[];
  ideas: Record<string, IdeasState>;
  onGenerate: (platform: string) => void;
}

export default function StrategyPanel({ scores, ideas, onGenerate }: StrategyPanelProps) {
  return (
    <div className="max-w-3xl space-y-3">
      {scores.map((s) => (
        <ScoreCard key={s.platform} s={s} ideas={ideas[s.platform]} onGenerate={() => onGenerate(s.platform)} />
      ))}
    </div>
  );
}

function ScoreCard({ s, ideas, onGenerate }: { s: PlatformScore; ideas: IdeasState; onGenerate: () => void }) {
  return (
    <div className="rounded-md border border-ink-700 bg-ink-850 p-3.5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="font-medium text-paper">{s.display_name}</span>
          {s.recommended && (
            <span className="rounded bg-clay-soft px-1.5 py-0.5 text-[11px] font-medium text-clay">推荐</span>
          )}
        </div>
        <span className="font-mono text-[13px] text-paper-dim">
          {s.score}
          <span className="text-paper-faint">/100</span>
        </span>
      </div>
      {/* 契合度条 */}
      <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-ink-800">
        <div className="h-full rounded-full bg-clay" style={{ width: `${s.score}%` }} />
      </div>
      <p className="mt-2 text-[13px] leading-relaxed text-paper-dim">{s.reason}</p>

      <div className="mt-3">
        {ideas === "loading" ? (
          <div className="flex items-center gap-1.5 text-[13px] text-paper-faint">
            <Loader2 size={14} className="animate-spin" /> 正在生成创意…
          </div>
        ) : ideas ? (
          <IdeasView ideas={ideas} />
        ) : (
          <button
            onClick={onGenerate}
            className="rounded border border-ink-600 px-2.5 py-1 text-[13px] font-medium text-paper-dim transition-colors hover:text-paper"
          >
            生成{s.display_name}创意
          </button>
        )}
      </div>
    </div>
  );
}

function IdeasView({ ideas }: { ideas: IdeasResult }) {
  const [copied, setCopied] = useState<string | null>(null);

  async function copy(text: string, key: string) {
    const ok = await copyText(text);
    if (ok) {
      setCopied(key);
      window.setTimeout(() => setCopied(null), 1500);
    }
  }

  if (ideas.error) {
    return <div className="text-[13px] text-red-400">生成失败：{ideas.error}</div>;
  }

  return (
    <div className="space-y-3 border-t border-ink-700 pt-3">
      <Section label="标题候选">
        <ul className="space-y-1">
          {ideas.titles.map((t, i) => (
            <li key={i} className="group flex items-start gap-2">
              <button
                onClick={() => copy(t, `t${i}`)}
                className="mt-0.5 shrink-0 text-paper-faint transition-colors hover:text-clay"
                title="复制标题"
              >
                {copied === `t${i}` ? <Check size={13} className="text-clay" /> : <Copy size={13} />}
              </button>
              <span className="text-[13px] text-paper">{t}</span>
            </li>
          ))}
        </ul>
      </Section>

      {ideas.hashtags.length > 0 && (
        <Section
          label="话题标签"
          action={
            <button
              onClick={() => copy(ideas.hashtags.map((h) => "#" + h).join(" "), "tags")}
              className="text-[11px] text-paper-faint transition-colors hover:text-clay"
            >
              {copied === "tags" ? "已复制" : "复制全部"}
            </button>
          }
        >
          <div className="flex flex-wrap gap-1.5">
            {ideas.hashtags.map((h) => (
              <span key={h} className="rounded bg-ink-800 px-2 py-0.5 text-[12px] text-paper-dim">
                #{h}
              </span>
            ))}
          </div>
        </Section>
      )}

      {ideas.cover_copy.length > 0 && (
        <Section label="封面文案">
          <ul className="space-y-1">
            {ideas.cover_copy.map((c, i) => (
              <li key={i} className="flex items-start gap-2">
                <button
                  onClick={() => copy(c, `c${i}`)}
                  className="mt-0.5 shrink-0 text-paper-faint transition-colors hover:text-clay"
                  title="复制文案"
                >
                  {copied === `c${i}` ? <Check size={13} className="text-clay" /> : <Copy size={13} />}
                </button>
                <span className="text-[13px] text-paper-dim">{c}</span>
              </li>
            ))}
          </ul>
        </Section>
      )}
    </div>
  );
}

function Section({ label, action, children }: { label: string; action?: ReactNode; children: ReactNode }) {
  return (
    <div>
      <div className="mb-1 flex items-center justify-between">
        <span className="text-[11px] font-medium tracking-[0.08em] text-paper-faint">{label}</span>
        {action}
      </div>
      {children}
    </div>
  );
}
