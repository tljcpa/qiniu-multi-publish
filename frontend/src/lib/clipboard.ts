// 剪贴板复制：三层兜底（见复盘 D-08）。
// 1) navigator.clipboard（需 HTTPS 安全上下文）
// 2) document.execCommand('copy')（旧浏览器兜底）
// 3) 都失败则返回 false，由调用方提示用户手动复制。

export async function copyText(text: string): Promise<boolean> {
  // 第一层：现代异步剪贴板 API
  if (navigator.clipboard && window.isSecureContext) {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch {
      // 落到下一层
    }
  }
  // 第二层：execCommand 兜底
  try {
    const ta = document.createElement("textarea");
    ta.value = text;
    ta.style.position = "fixed";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.focus();
    ta.select();
    const ok = document.execCommand("copy");
    document.body.removeChild(ta);
    return ok;
  } catch {
    return false;
  }
}
