// 手机外壳组件：圆角边框 + 刘海 + 状态栏，内部是可滚动的平台预览内容。
// 让每个平台的适配结果以"贴进真机后的样子"呈现（亮点4：所见即所得预览）。

import type { ReactNode } from "react";

interface PhoneFrameProps {
  // 状态栏右上角运营商/标题区域文字（一般放平台名）
  statusLabel: string;
  // 状态栏文字与图标颜色是否用深色（浅色顶栏用深色字）
  darkStatus?: boolean;
  // 顶栏背景色（平台品牌色或白）
  topBarColor?: string;
  children: ReactNode;
}

export default function PhoneFrame({
  statusLabel,
  darkStatus = true,
  topBarColor = "#ffffff",
  children,
}: PhoneFrameProps) {
  const statusColor = darkStatus ? "#1f2937" : "#ffffff";
  return (
    <div className="w-[300px] shrink-0">
      <div className="rounded-[2.4rem] border-[11px] border-gray-900 bg-gray-900 shadow-2xl">
        <div className="relative flex h-[600px] flex-col overflow-hidden rounded-[1.7rem] bg-white">
          {/* 刘海 */}
          <div className="absolute left-1/2 top-0 z-20 h-[22px] w-[120px] -translate-x-1/2 rounded-b-2xl bg-gray-900" />
          {/* 状态栏 */}
          <div
            className="flex items-center justify-between px-5 pt-1.5 pb-1 text-[11px] font-medium"
            style={{ backgroundColor: topBarColor, color: statusColor }}
          >
            <span>9:41</span>
            <span className="max-w-[110px] truncate">{statusLabel}</span>
            <span className="flex items-center gap-0.5">
              <Signal color={statusColor} />
              <Battery color={statusColor} />
            </span>
          </div>
          {/* 内容滚动区 */}
          <div className="flex-1 overflow-y-auto">{children}</div>
        </div>
      </div>
    </div>
  );
}

function Signal({ color }: { color: string }) {
  return (
    <svg width="15" height="11" viewBox="0 0 18 12" fill={color}>
      <rect x="0" y="8" width="3" height="4" rx="1" />
      <rect x="5" y="5" width="3" height="7" rx="1" />
      <rect x="10" y="2" width="3" height="10" rx="1" />
      <rect x="15" y="0" width="3" height="12" rx="1" opacity="0.4" />
    </svg>
  );
}

function Battery({ color }: { color: string }) {
  return (
    <svg width="22" height="11" viewBox="0 0 26 12" fill="none">
      <rect x="0.5" y="0.5" width="22" height="11" rx="2.5" stroke={color} opacity="0.5" />
      <rect x="2" y="2" width="16" height="8" rx="1.2" fill={color} />
      <rect x="23.5" y="3.5" width="2" height="5" rx="1" fill={color} opacity="0.5" />
    </svg>
  );
}
