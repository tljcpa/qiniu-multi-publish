// 一键复制 + 跳转闭环（亮点5）。
// 主操作"复制并前往发布"：先写剪贴板，再新标签打开平台官方编辑页；
// 真正"按下发布"留在用户手里、平台官方界面里（产品定位 D-01）。

import { useState } from "react";
import { Copy, ExternalLink, Check } from "lucide-react";
import type { PlatformResult } from "../lib/api";
import { copyText } from "../lib/clipboard";

type CopyState = "idle" | "copied" | "failed";

export default function PublishActions({ result }: { result: PlatformResult }) {
  const [copyState, setCopyState] = useState<CopyState>("idle");
  const [manualText, setManualText] = useState<string | null>(null);

  const intent = result.publish_intent;
  if (!intent) {
    return null;
  }

  async function doCopy(): Promise<boolean> {
    const ok = await copyText(intent!.clipboard);
    if (ok) {
      setCopyState("copied");
      window.setTimeout(() => setCopyState("idle"), 2000);
    } else {
      setCopyState("failed");
      setManualText(intent!.clipboard);
    }
    return ok;
  }

  async function copyAndGo() {
    await doCopy();
    window.open(intent!.url, "_blank", "noopener,noreferrer");
  }

  return (
    <div className="flex w-[300px] flex-col gap-1.5">
      <button
        onClick={copyAndGo}
        className="flex items-center justify-center gap-1.5 rounded bg-clay py-2 text-sm font-medium text-white transition-colors hover:bg-clay-hover"
      >
        <ExternalLink size={14} />
        复制并前往{result.display_name}发布
      </button>
      <button
        onClick={doCopy}
        className="flex items-center justify-center gap-1.5 rounded border border-ink-600 py-1.5 text-xs font-medium text-paper-dim transition-colors hover:border-ink-600 hover:text-paper"
      >
        {copyState === "copied" ? (
          <>
            <Check size={13} className="text-clay" /> 已复制到剪贴板
          </>
        ) : (
          <>
            <Copy size={13} /> 仅复制内容
          </>
        )}
      </button>
      {copyState === "failed" && manualText && (
        <div className="rounded border border-ink-600 bg-ink-800 p-2 text-xs text-paper-dim">
          自动复制被浏览器拦截，请手动选择下方内容复制：
          <textarea
            readOnly
            value={manualText}
            className="mt-1 h-24 w-full resize-none rounded border border-ink-700 bg-ink-900 p-1.5 font-mono text-[11px] text-paper-dim"
            onFocus={(e) => e.currentTarget.select()}
          />
        </div>
      )}
    </div>
  );
}
