// 公众号文章预览：白底、账号头部、加粗标题、引言、正文、底部"赞/在看"。
import { Eye, ThumbsUp, MessageSquare } from "lucide-react";
import type { PlatformResult } from "../../lib/api";
import { renderMarkdown } from "../../lib/markdown";

export default function WechatPreview({ result }: { result: PlatformResult }) {
  return (
    <div className="px-5 pb-6 pt-3 text-[15px] leading-relaxed text-gray-800">
      <h1 className="mb-3 text-[21px] font-bold leading-snug text-gray-900">{result.title}</h1>
      {/* 账号信息行 */}
      <div className="mb-4 flex items-center gap-2">
        <div className="flex h-9 w-9 items-center justify-center rounded-md bg-wechat text-sm font-bold text-white">
          公
        </div>
        <div className="leading-tight">
          <div className="text-[14px] font-medium text-[#576b95]">我的公众号</div>
          <div className="text-[11px] text-gray-400">今天 · 北京</div>
        </div>
        <button className="ml-auto rounded-md bg-wechat px-3 py-1 text-xs font-medium text-white">
          关注
        </button>
      </div>
      {result.summary && (
        <p className="mb-3 border-l-2 border-gray-200 pl-3 text-[13px] italic text-gray-500">
          {result.summary}
        </p>
      )}
      <div
        className="preview-body"
        dangerouslySetInnerHTML={{ __html: renderMarkdown(result.content) }}
      />
      {/* 底部互动 */}
      <div className="mt-6 flex items-center justify-center gap-7 border-t border-gray-100 pt-4 text-gray-400">
        <span className="flex items-center gap-1 text-xs"><ThumbsUp size={16} /> 赞</span>
        <span className="flex items-center gap-1 text-xs text-wechat"><Eye size={16} /> 在看</span>
        <span className="flex items-center gap-1 text-xs"><MessageSquare size={16} /> 评论</span>
      </div>
    </div>
  );
}
