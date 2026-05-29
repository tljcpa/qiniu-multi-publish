// 预览面板：把每个平台结果套进手机壳，用对应平台的高保真预览组件渲染。
// 平台 -> 组件的映射；未知平台回退到通用渲染，保证新增平台也能显示。

import PhoneFrame from "./PhoneFrame";
import PublishActions from "./PublishActions";
import WechatPreview from "./previews/WechatPreview";
import ZhihuPreview from "./previews/ZhihuPreview";
import BilibiliPreview from "./previews/BilibiliPreview";
import XhsPreview from "./previews/XhsPreview";
import type { PlatformResult } from "../lib/api";
import { renderMarkdown } from "../lib/markdown";

// 各平台手机壳顶栏外观
const CHROME: Record<string, { topBar: string; dark: boolean }> = {
  wechat: { topBar: "#ffffff", dark: true },
  zhihu: { topBar: "#ffffff", dark: true },
  bilibili: { topBar: "#ffffff", dark: true },
  xhs: { topBar: "#FF2442", dark: false },
};

function renderInner(result: PlatformResult) {
  switch (result.platform) {
    case "wechat":
      return <WechatPreview result={result} />;
    case "zhihu":
      return <ZhihuPreview result={result} />;
    case "bilibili":
      return <BilibiliPreview result={result} />;
    case "xhs":
      return <XhsPreview result={result} />;
    default:
      // 通用回退：新增平台未提供专属预览时仍可显示
      return (
        <div className="px-5 py-4 text-[15px] leading-relaxed text-gray-800">
          <h1 className="mb-3 text-lg font-bold">{result.title}</h1>
          <div className="preview-body" dangerouslySetInnerHTML={{ __html: renderMarkdown(result.content) }} />
        </div>
      );
  }
}

export default function PreviewPanel({ results }: { results: PlatformResult[] }) {
  return (
    <div className="flex gap-6 overflow-x-auto pb-4">
      {results.map((r) => {
        const chrome = CHROME[r.platform] ?? { topBar: "#ffffff", dark: true };
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
                {renderInner(r)}
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
