// 用户模型偏好：按平台记忆"上次选了哪个模型"，存 localStorage（见复盘 D-10）。
// 下次对该平台对比时默认勾选偏好模型，体现"模型选择回流"的设计感。

const KEY = "mp_model_pref_v1";

type PrefMap = Record<string, { provider: string; model: string; label: string }>;

function readAll(): PrefMap {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) {
      return {};
    }
    return JSON.parse(raw) as PrefMap;
  } catch {
    return {};
  }
}

export function getPreferredModel(platform: string) {
  return readAll()[platform] ?? null;
}

export function setPreferredModel(
  platform: string,
  pref: { provider: string; model: string; label: string }
) {
  const all = readAll();
  all[platform] = pref;
  try {
    localStorage.setItem(KEY, JSON.stringify(all));
  } catch {
    // localStorage 不可用（隐私模式等）时静默忽略，不影响主流程
  }
}
