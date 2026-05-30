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
        // 手机壳：近黑机身 + 近白屏幕（避免纯黑纯白）
        bezel: "#100e0c",
        screen: "#fbfaf7",
        // 平台品牌色（预览内部用，保持真实）
        wechat: "#07C160",
        zhihu: "#0066FF",
        bilibili: "#FB7299",
        xhs: "#FF2442",
      },
      fontFamily: {
        // 正文/UI：思源黑体（写作者工作台）
        sans: ['"Noto Sans SC"', '"PingFang SC"', '"Microsoft YaHei"', "sans-serif"],
        // 标题：思源宋体（编辑/出版气质）
        serif: ['"Noto Serif SC"', '"Songti SC"', '"SimSun"', "serif"],
        // 数据/遥测用系统等宽（非 Inter/Roboto，制造工作台精度感）
        mono: ["ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
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
