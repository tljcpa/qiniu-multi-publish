// 多模型对比结果面板：同一平台、多个模型的适配结果并排，带耗时与"用这个模型"。
import { Clock, Check, Star } from "lucide-react";
import PhoneFrame from "./PhoneFrame";
import PublishActions from "./PublishActions";
import { getChrome, renderPlatformInner } from "./previews/render";
import type { CompareVariantResult } from "../lib/api";

interface ComparePanelProps {
  variants: CompareVariantResult[];
  preferredKey: string | null;
  onPick: (v: CompareVariantResult) => void;
}

export default function ComparePanel({ variants, preferredKey, onPick }: ComparePanelProps) {
  return (
    <div className="flex gap-5 overflow-x-auto pb-4">
      {variants.map((v) => {
        const chrome = getChrome(v.result.platform);
        const key = `${v.provider}:${v.model}`;
        const preferred = key === preferredKey;
        return (
          <div key={v.label} className="flex flex-col items-center gap-2.5">
            <div className="flex w-[300px] items-center justify-between">
              <span className="flex items-center gap-1.5 text-sm font-semibold text-paper">
                {v.label}
                {preferred && (
                  <span className="flex items-center gap-0.5 rounded bg-clay-soft px-1.5 py-0.5 font-mono text-[10px] font-medium text-clay">
                    <Star size={9} /> 偏好
                  </span>
                )}
              </span>
              <span className="flex items-center gap-1 font-mono text-[11px] text-paper-faint">
                <Clock size={11} /> {(v.latency_ms / 1000).toFixed(1)}s
              </span>
            </div>

            {v.result.error ? (
              <PhoneFrame statusLabel={v.label} topBarColor="#ffffff" darkStatus>
                <div className="flex h-full flex-col items-center justify-center px-6 text-center text-sm text-red-500">
                  适配失败
                  <span className="mt-1 text-xs text-gray-400">{v.result.error}</span>
                </div>
              </PhoneFrame>
            ) : (
              <PhoneFrame statusLabel={v.label} topBarColor={chrome.topBar} darkStatus={chrome.dark}>
                {renderPlatformInner(v.result)}
              </PhoneFrame>
            )}

            {!v.result.error && (
              <>
                <button
                  onClick={() => onPick(v)}
                  className={`flex w-[300px] items-center justify-center gap-1.5 rounded py-2 text-sm font-medium transition-colors ${
                    preferred
                      ? "bg-clay text-white hover:bg-clay-hover"
                      : "border border-ink-600 text-paper-dim hover:text-paper"
                  }`}
                >
                  {preferred ? <Check size={14} /> : <Star size={14} />}
                  {preferred ? "已设为该平台偏好" : "用这个模型"}
                </button>
                <PublishActions result={v.result} />
              </>
            )}
          </div>
        );
      })}
    </div>
  );
}
