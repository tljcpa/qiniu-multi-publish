/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // 暖墨灰深色（warm graphite ink）—— 刻意避开 slate/zinc 冷灰默认
        ink: {
          950: "#121110",
          900: "#191713", // app 背景
          850: "#201d18", // 面板
          800: "#272219", // 抬升面/输入
          700: "#352f25", // 边框
          600: "#463e30", // 强边框
        },
        // 单一陶土色强调（呼应内容/出版编辑气质）—— 非靛蓝/紫
        clay: {
          DEFAULT: "#c2693f",
          hover: "#d3764b",
          soft: "#2e231b", // 极淡背景着色
        },
        // 暖白文字层级
        paper: {
          DEFAULT: "#ece6da",
          dim: "#a8a08f",
          faint: "#7b7363",
        },
        // 平台品牌色（预览内部用，保持真实）
        wechat: "#07C160",
        zhihu: "#0066FF",
        bilibili: "#FB7299",
        xhs: "#FF2442",
      },
      fontFamily: {
        // 拉丁/UI 用 IBM Plex Sans（刻意非 Inter 默认），CJK 走系统原生
        sans: [
          '"IBM Plex Sans"',
          '"PingFang SC"',
          '"Microsoft YaHei"',
          '"Noto Sans SC"',
          "sans-serif",
        ],
        // 元数据/标签/数字用等宽，制造工具遥测质感
        mono: ['"IBM Plex Mono"', "SFMono-Regular", "ui-monospace", "monospace"],
      },
      borderRadius: {
        // 克制圆角
        DEFAULT: "4px",
        md: "5px",
        lg: "7px",
      },
    },
  },
  plugins: [],
};
