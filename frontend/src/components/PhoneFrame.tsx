// 手机外壳：近黑机身 + 灵动岛刘海 + 侧键 + 底部 Home 指示条 + 近白屏幕。
// 这是本项目最强的视觉签名，刻意做"重"：厚机身、接地阴影、真实细节。
// 避免纯黑纯白（机身 bezel #100e0c，屏幕 screen #fbfaf7）。

import type { ReactNode } from "react";

interface PhoneFrameProps {
  statusLabel: string;
  darkStatus?: boolean;
  topBarColor?: string;
  children: ReactNode;
}

export default function PhoneFrame({
  statusLabel,
  darkStatus = true,
  topBarColor = "#fbfaf7",
  children,
}: PhoneFrameProps) {
  const statusColor = darkStatus ? "#1f2937" : "#ffffff";
  return (
    <div className="w-[300px] shrink-0">
      <div className="relative">
        {/* 侧键（机身厚度感） */}
        <div className="absolute -left-[2px] top-[112px] h-8 w-[3px] rounded-l-sm bg-[#2a251e]" />
        <div className="absolute -left-[2px] top-[156px] h-12 w-[3px] rounded-l-sm bg-[#2a251e]" />
        <div className="absolute -right-[2px] top-[140px] h-16 w-[3px] rounded-r-sm bg-[#2a251e]" />

        {/* 机身：厚边框 + 接地阴影 */}
        <div className="rounded-[2.6rem] bg-bezel p-[3px] shadow-[0_30px_55px_-18px_rgba(0,0,0,0.78)] ring-1 ring-white/[0.06]">
          <div className="rounded-[2.45rem] border border-black/50 bg-bezel p-[9px]">
            <div
              className="relative flex h-[600px] flex-col overflow-hidden rounded-[1.95rem] bg-screen"
              aria-label={`${statusLabel}预览`}
            >
              {/* 灵动岛 */}
              <div className="absolute left-1/2 top-[9px] z-20 flex h-[24px] w-[86px] -translate-x-1/2 items-center justify-end rounded-full bg-black pr-2.5">
                <span className="h-[7px] w-[7px] rounded-full bg-[#15151b] ring-1 ring-white/15" />
              </div>

              {/* 状态栏（真实：时间 + 信号/电量） */}
              <div
                className="flex items-center justify-between px-5 pt-2 pb-1 text-[11px] font-medium"
                style={{ backgroundColor: topBarColor, color: statusColor }}
              >
                <span className="tabular-nums">9:41</span>
                <span className="flex items-center gap-1">
                  <Signal color={statusColor} />
                  <Battery color={statusColor} />
                </span>
              </div>

              {/* 内容滚动区 */}
              <div className="flex-1 overflow-y-auto">{children}</div>

              {/* Home 指示条 */}
              <div className="pointer-events-none absolute bottom-[6px] left-1/2 z-20 h-[5px] w-[108px] -translate-x-1/2 rounded-full bg-black/25" />
            </div>
          </div>
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
