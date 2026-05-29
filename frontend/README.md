# 前端

React + Vite + TypeScript + Tailwind + Tiptap 的多平台内容适配界面。

## 结构

- `src/components/Editor.tsx` — Tiptap 富文本编辑器，输出 Markdown
- `src/lib/api.ts` — 后端 API 客户端（/platforms、/adapt）
- `src/App.tsx` — 主界面：标题/标签输入 + 编辑器 + 平台多选 + 一键适配 + 结果区

## 开发 / 构建

> 注意：构建在 Azure VM 上进行，本机内存受限不跑 npm。

```bash
npm install
npm run dev      # 开发（代理 /adapt、/platforms 到本地 8082）
npm run build    # 产出 dist/，由 Caddy 静态托管
```

生产态前端用同源相对路径调用后端，由 Caddy 按路径反代到后端 8082。
平台风格预览（PR12）与一键复制 + 跳转（PR13）在后续 PR 完善。
