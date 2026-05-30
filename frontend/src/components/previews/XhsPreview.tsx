// 小红书笔记预览：顶部封面图(用渐变占位+标题文案模拟)、正文 emoji、红色话题标签、底部点赞。
import { Heart, MessageCircle, Star, Share } from "lucide-react";
import type { PlatformResult } from "../../lib/api";
import { renderMarkdown } from "../../lib/markdown";

export default function XhsPreview({ result }: { result: PlatformResult }) {
  return (
    <div className="flex h-full flex-col text-[14px] text-gray-800">
      {/* 封面：小红书图片优先，这里用品牌色实底 + 标题文案模拟封面（不用渐变） */}
      <div className="relative flex aspect-[3/4] w-full items-center justify-center bg-xhs px-5 text-center">
        <span className="text-[19px] font-extrabold leading-snug text-white drop-shadow">
          {result.title}
        </span>
        <span className="absolute bottom-2 right-3 rounded-full bg-black/20 px-2 py-0.5 text-[10px] text-white">
          1/3
        </span>
      </div>
      {/* 正文 */}
      <div className="flex-1 overflow-y-auto px-4 py-3">
        <div className="mb-2 flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-full bg-xhs text-xs font-bold text-white">
            薯
          </div>
          <span className="text-[13px] font-medium text-gray-700">小红书博主</span>
          <button className="ml-auto rounded-full bg-xhs px-3 py-0.5 text-xs font-medium text-white">关注</button>
        </div>
        <h2 className="mb-1 text-[15px] font-bold text-gray-900">{result.title}</h2>
        <div
          className="preview-body preview-body-xhs"
          dangerouslySetInnerHTML={{ __html: renderMarkdown(result.content) }}
        />
        {result.hashtags.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-x-2 gap-y-1 text-[13px] font-medium text-[#3a5b9c]">
            {result.hashtags.map((t) => (
              <span key={t}>#{t}</span>
            ))}
          </div>
        )}
      </div>
      {/* 底部互动栏 */}
      <div className="flex items-center gap-4 border-t border-gray-100 px-4 py-2.5 text-gray-500">
        <span className="flex items-center gap-1 text-xs"><Heart size={17} className="text-xhs" /> 1.2k</span>
        <span className="flex items-center gap-1 text-xs"><Star size={17} /> 328</span>
        <span className="flex items-center gap-1 text-xs"><MessageCircle size={17} /> 56</span>
        <span className="ml-auto flex items-center gap-1 text-xs"><Share size={17} /></span>
      </div>
    </div>
  );
}
