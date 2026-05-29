// B 站专栏预览：白底、UP 主行、加粗标题、正文、底部粉色"点赞/投币/收藏"三连。
import { ThumbsUp, Coins, Star } from "lucide-react";
import type { PlatformResult } from "../../lib/api";
import { renderMarkdown } from "../../lib/markdown";

export default function BilibiliPreview({ result }: { result: PlatformResult }) {
  return (
    <div className="px-5 pb-6 pt-3 text-[15px] leading-relaxed text-gray-800">
      <h1 className="mb-3 text-[20px] font-bold leading-snug text-gray-900">{result.title}</h1>
      {/* UP 主行 */}
      <div className="mb-4 flex items-center gap-2">
        <div className="flex h-9 w-9 items-center justify-center rounded-full bg-bilibili text-sm font-bold text-white">
          UP
        </div>
        <div className="leading-tight">
          <div className="text-[14px] font-medium text-bilibili">本 UP 主</div>
          <div className="text-[11px] text-gray-400">2.3 万粉丝 · 刚刚发布</div>
        </div>
        <button className="ml-auto rounded-md bg-bilibili px-3 py-1 text-xs font-medium text-white">
          + 关注
        </button>
      </div>
      <div
        className="preview-body"
        dangerouslySetInnerHTML={{ __html: renderMarkdown(result.content) }}
      />
      {/* 底部一键三连 */}
      <div className="mt-6 flex items-center justify-around border-t border-gray-100 pt-4 text-gray-500">
        <span className="flex flex-col items-center gap-0.5 text-[11px]"><ThumbsUp size={20} className="text-bilibili" /> 点赞</span>
        <span className="flex flex-col items-center gap-0.5 text-[11px]"><Coins size={20} className="text-bilibili" /> 投币</span>
        <span className="flex flex-col items-center gap-0.5 text-[11px]"><Star size={20} className="text-bilibili" /> 收藏</span>
      </div>
    </div>
  );
}
