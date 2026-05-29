// 预览面板：每个平台结果套进手机壳 + 一行 mono 遥测（字数/标签/耗时/模型）。
// 流式态显示逐字打字（原始文本 + 光标）；完成后切换为高保真平台预览。
import PhoneFrame from "./PhoneFrame";
import PublishActions from "./PublishActions";
import { getChrome, renderPlatformInner } from "./previews/render";
import type { PlatformResult } from "../lib/api";

export default function PreviewPanel({ results }: { results: PlatformResult[] }) {
  return (
    <div className="flex gap-5 overflow-x-auto pb-4">
      {results.map((r) => {
        const chrome = getChrome(r.platform);
        return (
          <div key={r.platform} className="flex flex-col items-center gap-2.5">
            {r.error ? (
              <PhoneFrame statusLabel={r.display_name} topBarColor="#ffffff" darkStatus>
                <div className="flex h-full flex-col items-center justify-center px-6 text-center text-sm text-red-500">
                  适配失败
                  <span className="mt-1 text-xs text-gray-400">{r.error}</span>
                </div>
              </PhoneFrame>
            ) : r.streaming ? (
              <PhoneFrame statusLabel={r.display_name} topBarColor={chrome.topBar} darkStatus={chrome.dark}>
                <div className="px-5 py-4 text-[14px] leading-relaxed text-gray-700">
                  <div className="mb-2 font-mono text-[11px] uppercase tracking-wide text-gray-400">generating</div>
                  <div className="typing-caret whitespace-pre-wrap break-words">{r.content}</div>
                </div>
              </PhoneFrame>
            ) : (
              <PhoneFrame statusLabel={r.display_name} topBarColor={chrome.topBar} darkStatus={chrome.dark}>
                {renderPlatformInner(r)}
              </PhoneFrame>
            )}
            <PlatformMeta result={r} />
            {!r.error && !r.streaming && <PublishActions result={r} />}
          </div>
        );
      })}
    </div>
  );
}

function PlatformMeta({ result }: { result: PlatformResult }) {
  return (
    <div className="flex w-[300px] items-center justify-between">
      <span className="text-sm font-semibold text-paper">{result.display_name}</span>
      {!result.error && (
        <span className="font-mono text-[11px] text-paper-faint">
          {result.streaming ? `${result.content.length}字…` : metaLine(result)}
        </span>
      )}
    </div>
  );
}

function metaLine(r: PlatformResult): string {
  const parts = [`${r.content.length}字`];
  if (r.hashtags.length > 0) {
    parts.push(`#${r.hashtags.length}`);
  }
  if (typeof r.elapsed_ms === "number" && r.elapsed_ms > 0) {
    parts.push(`${(r.elapsed_ms / 1000).toFixed(1)}s`);
  }
  if (r.model) {
    parts.push(r.model);
  }
  return parts.join(" · ");
}
