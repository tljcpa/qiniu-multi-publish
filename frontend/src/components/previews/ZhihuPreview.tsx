// 知乎文章预览：白底、作者行带蓝色关注、加粗标题、正文、底部蓝色"赞同"。
import { ThumbsUp, MessageSquare, Star } from "lucide-react";
import type { PlatformResult } from "../../lib/api";
import { renderMarkdown } from "../../lib/markdown";

export default function ZhihuPreview({ result }: { result: PlatformResult }) {
  return (
    <div className="px-5 pb-6 pt-3 text-[15px] leading-relaxed text-gray-800">
      <h1 className="mb-3 text-[20px] font-bold leading-snug text-gray-900">{result.title}</h1>
      {/* 作者行 */}
      <div className="mb-4 flex items-center gap-2">
        <div className="flex h-9 w-9 items-center justify-center rounded-full bg-zhihu text-sm font-bold text-white">
          知
        </div>
        <div className="leading-tight">
          <div className="text-[14px] font-medium text-gray-900">知乎答主</div>
          <div className="text-[11px] text-gray-400">理性讨论，欢迎补充</div>
        </div>
        <button className="ml-auto rounded-full bg-zhihu px-3.5 py-1 text-xs font-medium text-white">
          + 关注
        </button>
      </div>
      <div
        className="preview-body preview-body-zhihu"
        dangerouslySetInnerHTML={{ __html: renderMarkdown(result.content) }}
      />
      {/* 底部互动 */}
      <div className="mt-6 flex items-center gap-4 border-t border-gray-100 pt-4">
        <span className="flex items-center gap-1 rounded-full bg-zhihu px-3 py-1.5 text-xs font-medium text-white">
          <ThumbsUp size={14} /> 赞同
        </span>
        <span className="flex items-center gap-1 text-xs text-gray-400"><MessageSquare size={15} /> 评论</span>
        <span className="ml-auto flex items-center gap-1 text-xs text-gray-400"><Star size={15} /> 收藏</span>
      </div>
    </div>
  );
}
