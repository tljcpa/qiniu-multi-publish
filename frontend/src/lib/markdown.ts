// Markdown 渲染：marked 解析 + DOMPurify 消毒，防 XSS。
// 预览区把适配后的正文（Markdown）渲染成 HTML 展示。

import { marked } from "marked";
import DOMPurify from "dompurify";

marked.setOptions({ breaks: true, gfm: true });

export function renderMarkdown(md: string): string {
  const raw = marked.parse(md ?? "", { async: false }) as string;
  return DOMPurify.sanitize(raw);
}
