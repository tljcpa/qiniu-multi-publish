// 后端 API 客户端与类型定义。
// 生产态用同源相对路径（Caddy 按路径反代到后端 8082）；可用 VITE_API_BASE 覆盖。

const API_BASE = import.meta.env.VITE_API_BASE ?? "";

export interface PlatformInfo {
  name: string;
  display_name: string;
  editor_url: string;
  preview_template: string;
  extension_guide: string;
}

export interface PublishIntent {
  clipboard: string;
  url: string;
}

export interface PlatformResult {
  platform: string;
  display_name: string;
  title: string;
  content: string;
  summary: string;
  hashtags: string[];
  model: string;
  preview_template: string;
  formatted: string;
  publish_intent: PublishIntent | null;
  error: string | null;
  // 前端流式态标记：true 表示该平台仍在逐字生成中
  streaming?: boolean;
  // 客户端测得的生成耗时（毫秒，流式从 meta 到 done）
  elapsed_ms?: number;
}

export interface ContentInput {
  title: string;
  body_md: string;
  tags: string[];
}

export interface AdaptRequest {
  content: ContentInput;
  platforms: string[];
  provider?: string;
  model?: string;
}

export async function fetchPlatforms(): Promise<PlatformInfo[]> {
  const resp = await fetch(`${API_BASE}/platforms`);
  if (!resp.ok) {
    throw new Error(`获取平台列表失败: ${resp.status}`);
  }
  return resp.json();
}

export async function adaptContent(req: AdaptRequest): Promise<PlatformResult[]> {
  const resp = await fetch(`${API_BASE}/adapt`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!resp.ok) {
    throw new Error(`适配请求失败: ${resp.status}`);
  }
  const data = await resp.json();
  return data.results as PlatformResult[];
}

// ---------------- 流式适配（SSE 打字机）----------------
export interface StreamHandlers {
  onMeta: (platform: string, displayName: string, previewTemplate: string) => void;
  onDelta: (platform: string, text: string) => void;
  onDone: (platform: string, result: PlatformResult) => void;
  onError: (platform: string, error: string) => void;
  onAllDone?: () => void;
}

export async function adaptStream(req: AdaptRequest, handlers: StreamHandlers): Promise<void> {
  const resp = await fetch(`${API_BASE}/adapt/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!resp.ok || !resp.body) {
    throw new Error(`流式适配请求失败: ${resp.status}`);
  }
  const reader = resp.body.getReader();
  const decoder = new TextDecoder();
  let buf = "";
  // 持续读取 SSE，按空行分帧
  for (;;) {
    const { done, value } = await reader.read();
    if (done) {
      break;
    }
    buf += decoder.decode(value, { stream: true });
    const frames = buf.split("\n\n");
    buf = frames.pop() ?? "";
    for (const frame of frames) {
      const dataLine = frame.split("\n").find((l) => l.startsWith("data: "));
      if (!dataLine) {
        continue;
      }
      const evt = JSON.parse(dataLine.slice(6));
      dispatchStreamEvent(evt, handlers);
    }
  }
}

function dispatchStreamEvent(evt: any, h: StreamHandlers) {
  switch (evt.type) {
    case "meta":
      h.onMeta(evt.platform, evt.display_name, evt.preview_template);
      break;
    case "delta":
      h.onDelta(evt.platform, evt.text);
      break;
    case "done":
      h.onDone(evt.platform, evt.result as PlatformResult);
      break;
    case "error":
      h.onError(evt.platform, evt.error);
      break;
    case "all_done":
      h.onAllDone?.();
      break;
    default:
      break;
  }
}

// ---------------- 多模型对比 ----------------
export interface ModelOption {
  label: string;
  provider: string;
  model: string;
}

export interface CompareVariant {
  label: string;
  provider: string;
  model: string | null;
}

export interface CompareVariantResult {
  label: string;
  provider: string;
  model: string;
  latency_ms: number;
  result: PlatformResult;
}

export interface CompareResponse {
  platform: string;
  display_name: string;
  variants: CompareVariantResult[];
}

export async function fetchModels(): Promise<ModelOption[]> {
  const resp = await fetch(`${API_BASE}/models`);
  if (!resp.ok) {
    throw new Error(`获取模型列表失败: ${resp.status}`);
  }
  return resp.json();
}

// ---------------- 发布策略 Agent ----------------
export interface PlatformScore {
  platform: string;
  display_name: string;
  score: number;
  reason: string;
  recommended: boolean;
}

export interface IdeasResult {
  platform: string;
  display_name: string;
  titles: string[];
  hashtags: string[];
  cover_copy: string[];
  model: string;
  error: string | null;
}

export async function fetchStrategy(content: ContentInput): Promise<PlatformScore[]> {
  const resp = await fetch(`${API_BASE}/strategy`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content }),
  });
  if (!resp.ok) {
    throw new Error(`策略分析失败: ${resp.status}`);
  }
  return (await resp.json()).scores as PlatformScore[];
}

export async function fetchIdeas(content: ContentInput, platform: string): Promise<IdeasResult> {
  const resp = await fetch(`${API_BASE}/ideas`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content, platform }),
  });
  if (!resp.ok) {
    throw new Error(`创意生成失败: ${resp.status}`);
  }
  return resp.json();
}

export async function compareModels(
  content: ContentInput,
  platform: string,
  variants: CompareVariant[]
): Promise<CompareResponse> {
  const resp = await fetch(`${API_BASE}/compare`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content, platform, variants }),
  });
  if (!resp.ok) {
    throw new Error(`对比请求失败: ${resp.status}`);
  }
  return resp.json();
}

// ---------------- 历史账户 ----------------

export interface HistoryItem {
  id: number;
  session_id: string;
  title: string;
  body_md: string;
  tags: string[];
  platforms: string[];
  results: PlatformResult[];
  created_at: string;
}

export interface SaveHistoryRequest {
  session_id: string;
  title: string;
  body_md: string;
  tags: string[];
  platforms: string[];
  results: PlatformResult[];
}

export async function fetchHistory(sessionId: string, limit = 20): Promise<HistoryItem[]> {
  const resp = await fetch(`${API_BASE}/history?session_id=${encodeURIComponent(sessionId)}&limit=${limit}`);
  if (!resp.ok) {
    throw new Error(`获取历史失败: ${resp.status}`);
  }
  return (await resp.json()).items as HistoryItem[];
}

export async function saveHistory(req: SaveHistoryRequest): Promise<HistoryItem> {
  const resp = await fetch(`${API_BASE}/history`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!resp.ok) {
    throw new Error(`保存历史失败: ${resp.status}`);
  }
  return resp.json();
}

export async function deleteHistory(itemId: number, sessionId: string): Promise<void> {
  const resp = await fetch(
    `${API_BASE}/history/${itemId}?session_id=${encodeURIComponent(sessionId)}`,
    { method: "DELETE" }
  );
  if (!resp.ok) {
    throw new Error(`删除历史失败: ${resp.status}`);
  }
}

// ---------------- AI 起草管线 ----------------

export interface DraftResult {
  title: string;
  body_md: string;
  tags: string[];
  draft_model: string;
  review_model: string;
}

export async function draftContent(topic: string): Promise<DraftResult> {
  const resp = await fetch(`${API_BASE}/draft`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ topic }),
  });
  if (!resp.ok) {
    const detail = await resp.json().catch(() => ({ detail: resp.statusText }));
    throw new Error(`起草失败: ${detail.detail ?? resp.status}`);
  }
  return resp.json();
}

// ---------------- 导出成品包 ----------------

export async function exportZip(results: PlatformResult[], title: string): Promise<void> {
  const resp = await fetch(`${API_BASE}/export`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ results, title }),
  });
  if (!resp.ok) {
    throw new Error(`导出失败: ${resp.status}`);
  }
  const blob = await resp.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  const slug = title.slice(0, 20).replace(/\s+/g, "-") || "content";
  a.download = `multi-publish-${slug}.zip`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
