// 多模型对比结果面板：同一平台、多个模型的适配结果并排，带耗时与"用这个模型"。
import { Clock, Check, Star } from "lucide-react";
import PhoneFrame from "./PhoneFrame";
import PublishActions from "./PublishActions";
import { getChrome, renderPlatformInner } from "./previews/render";
import type { CompareVariantResult } from "../lib/api";

interface ComparePanelProps {
  variants: CompareVariantResult[];
  // 当前平台已偏好的模型（provider:model），用于高亮
  preferredKey: string | null;
  onPick: (v: CompareVariantResult) => void;
}

export default function ComparePanel({ variants, preferredKey, onPick }: ComparePanelProps) {
  return (
    <div className="flex gap-6 overflow-x-auto pb-4">
      {variants.map((v) => {
        const chrome = getChrome(v.result.platform);
        const key = `${v.provider}:${v.model}`;
        const preferred = key === preferredKey;
        return (
          <div key={v.label} className="flex flex-col items-center gap-3">
            {/* 模型标签 + 耗时 */}
            <div className="flex w-[300px] items-center justify-between">
              <span className="flex items-center gap-1.5 text-sm font-semibold text-gray-800">
                {v.label}
                {preferred && (
                  <span className="flex items-center gap-0.5 rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-medium text-amber-700">
                    <Star size={10} /> 偏好
                  </span>
                )}
              </span>
              <span className="flex items-center gap-1 text-xs text-gray-400">
                <Clock size={12} /> {(v.latency_ms / 1000).toFixed(1)}s
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
                  className={`flex w-[300px] items-center justify-center gap-1.5 rounded-lg py-2 text-sm font-medium transition-colors ${
                    preferred
                      ? "bg-amber-500 text-white hover:bg-amber-600"
                      : "border border-gray-300 text-gray-700 hover:border-gray-400"
                  }`}
                >
                  {preferred ? <Check size={15} /> : <Star size={15} />}
                  {preferred ? "已设为该平台偏好模型" : "用这个模型"}
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
