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
