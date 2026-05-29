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
