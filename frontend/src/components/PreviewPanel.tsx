// 预览面板：把每个平台结果套进手机壳，用对应平台的高保真预览组件渲染。
import PhoneFrame from "./PhoneFrame";
import PublishActions from "./PublishActions";
import { getChrome, renderPlatformInner } from "./previews/render";
import type { PlatformResult } from "../lib/api";

export default function PreviewPanel({ results }: { results: PlatformResult[] }) {
  return (
    <div className="flex gap-6 overflow-x-auto pb-4">
      {results.map((r) => {
        const chrome = getChrome(r.platform);
        return (
          <div key={r.platform} className="flex flex-col items-center gap-3">
            {r.error ? (
              <PhoneFrame statusLabel={r.display_name} topBarColor="#ffffff" darkStatus>
                <div className="flex h-full flex-col items-center justify-center px-6 text-center text-sm text-red-500">
                  适配失败
                  <span className="mt-1 text-xs text-gray-400">{r.error}</span>
                </div>
              </PhoneFrame>
            ) : (
              <PhoneFrame statusLabel={r.display_name} topBarColor={chrome.topBar} darkStatus={chrome.dark}>
                {renderPlatformInner(r)}
              </PhoneFrame>
            )}
            <div className="text-sm font-semibold text-gray-700">{r.display_name}</div>
            {!r.error && <PublishActions result={r} />}
          </div>
        );
      })}
    </div>
  );
}
