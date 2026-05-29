// 平台 -> 预览组件 的共享映射，供 PreviewPanel（一键适配）与 ComparePanel（多模型对比）复用。
import WechatPreview from "./WechatPreview";
import ZhihuPreview from "./ZhihuPreview";
import BilibiliPreview from "./BilibiliPreview";
import XhsPreview from "./XhsPreview";
import type { PlatformResult } from "../../lib/api";
import { renderMarkdown } from "../../lib/markdown";

// 各平台手机壳顶栏外观
export const CHROME: Record<string, { topBar: string; dark: boolean }> = {
  wechat: { topBar: "#ffffff", dark: true },
  zhihu: { topBar: "#ffffff", dark: true },
  bilibili: { topBar: "#ffffff", dark: true },
  xhs: { topBar: "#FF2442", dark: false },
};

export function getChrome(name: string) {
  return CHROME[name] ?? { topBar: "#ffffff", dark: true };
}

export function renderPlatformInner(result: PlatformResult) {
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
