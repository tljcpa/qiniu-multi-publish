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
      // 复制失败：把内容暴露出来让用户手动复制，绝不假装成功
      setManualText(intent!.clipboard);
    }
    return ok;
  }

  async function copyAndGo() {
    await doCopy();
    // 无论复制成功与否都打开编辑页；失败时下方手动复制框兜底
    window.open(intent!.url, "_blank", "noopener,noreferrer");
  }

  return (
    <div className="flex w-[300px] flex-col gap-2">
      <button
        onClick={copyAndGo}
        className="flex items-center justify-center gap-1.5 rounded-lg bg-gray-900 py-2 text-sm font-medium text-white transition-colors hover:bg-gray-800"
      >
        <ExternalLink size={15} />
        复制并前往{result.display_name}发布
      </button>
      <button
        onClick={doCopy}
        className="flex items-center justify-center gap-1.5 rounded-lg border border-gray-300 py-1.5 text-xs font-medium text-gray-600 transition-colors hover:border-gray-400"
      >
        {copyState === "copied" ? (
          <>
            <Check size={14} className="text-green-600" /> 已复制到剪贴板
          </>
        ) : (
          <>
            <Copy size={14} /> 仅复制内容
          </>
        )}
      </button>
      {copyState === "failed" && manualText && (
        <div className="rounded-lg bg-amber-50 p-2 text-xs text-amber-700">
          自动复制被浏览器拦截，请手动选择下方内容复制：
          <textarea
            readOnly
            value={manualText}
            className="mt-1 h-24 w-full resize-none rounded border border-amber-200 bg-white p-1.5 text-[11px] text-gray-700"
            onFocus={(e) => e.currentTarget.select()}
          />
        </div>
      )}
    </div>
  );
}
