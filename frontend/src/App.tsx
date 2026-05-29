import { useEffect, useState } from "react";
import { Sparkles, Loader2, Send, GitCompare } from "lucide-react";
import Editor from "./components/Editor";
import PreviewPanel from "./components/PreviewPanel";
import ComparePanel from "./components/ComparePanel";
import {
  adaptContent,
  compareModels,
  fetchModels,
  fetchPlatforms,
  type CompareVariantResult,
  type ModelOption,
  type PlatformInfo,
  type PlatformResult,
} from "./lib/api";
import { getPreferredModel, setPreferredModel } from "./lib/preferences";

type Mode = "adapt" | "compare";

export default function App() {
  const [title, setTitle] = useState("");
  const [tagsInput, setTagsInput] = useState("");
  const [bodyMd, setBodyMd] = useState("");

  const [platforms, setPlatforms] = useState<PlatformInfo[]>([]);
  const [models, setModels] = useState<ModelOption[]>([]);

  const [mode, setMode] = useState<Mode>("adapt");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // adapt 模式
  const [selected, setSelected] = useState<string[]>([]);
  const [results, setResults] = useState<PlatformResult[]>([]);

  // compare 模式
  const [comparePlatform, setComparePlatform] = useState("");
  const [selectedModels, setSelectedModels] = useState<string[]>([]);
  const [compareResults, setCompareResults] = useState<CompareVariantResult[]>([]);
  const [preferredKey, setPreferredKey] = useState<string | null>(null);

  useEffect(() => {
    fetchPlatforms()
      .then((list) => {
        setPlatforms(list);
        setSelected(list.map((p) => p.name));
        if (list.length > 0) {
          setComparePlatform(list[0].name);
        }
      })
      .catch((e) => setError(String(e)));
    fetchModels()
      .then((list) => {
        setModels(list);
        // 默认选前两个模型对比
        setSelectedModels(list.slice(0, 2).map((m) => `${m.provider}:${m.model}`));
      })
      .catch((e) => setError(String(e)));
  }, []);

  // 切换对比平台时，载入该平台的偏好高亮
  useEffect(() => {
    if (!comparePlatform) {
      return;
    }
    const pref = getPreferredModel(comparePlatform);
    setPreferredKey(pref ? `${pref.provider}:${pref.model}` : null);
  }, [comparePlatform]);

  function buildContent() {
    const tags = tagsInput
      .split(/[,，\s]+/)
      .map((t) => t.trim())
      .filter(Boolean);
    return { title, body_md: bodyMd, tags };
  }

  function ensureInput(): boolean {
    setError(null);
    if (!title.trim() && !bodyMd.trim()) {
      setError("请先输入标题或正文");
      return false;
    }
    return true;
  }

  async function handleAdapt() {
    if (!ensureInput()) {
      return;
    }
    if (selected.length === 0) {
      setError("请至少选择一个平台");
      return;
    }
    setLoading(true);
    setResults([]);
    try {
      const res = await adaptContent({ content: buildContent(), platforms: selected });
      setResults(res);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }

  async function handleCompare() {
    if (!ensureInput()) {
      return;
    }
    if (selectedModels.length < 2) {
      setError("请至少选择 2 个模型进行对比");
      return;
    }
    setLoading(true);
    setCompareResults([]);
    try {
      const variants = selectedModels
        .map((key) => models.find((m) => `${m.provider}:${m.model}` === key))
        .filter((m): m is ModelOption => Boolean(m))
        .map((m) => ({ label: m.label, provider: m.provider, model: m.model }));
      const resp = await compareModels(buildContent(), comparePlatform, variants);
      setCompareResults(resp.variants);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }

  function pickModel(v: CompareVariantResult) {
    setPreferredModel(comparePlatform, { provider: v.provider, model: v.model, label: v.label });
    setPreferredKey(`${v.provider}:${v.model}`);
  }

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900">
      <Header />
      <main className="mx-auto max-w-7xl px-4 py-6">
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          {/* 左：输入 + 控制 */}
          <section className="flex flex-col gap-4">
            <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
              <input
                className="w-full border-0 text-xl font-semibold placeholder-gray-300 focus:outline-none focus:ring-0"
                placeholder="输入标题…"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
              />
              <input
                className="mt-2 w-full border-0 text-sm text-gray-500 placeholder-gray-300 focus:outline-none focus:ring-0"
                placeholder="标签，用逗号分隔（如：效率，成长）"
                value={tagsInput}
                onChange={(e) => setTagsInput(e.target.value)}
              />
            </div>

            <ModeToggle mode={mode} onChange={setMode} />

            {mode === "adapt" && (
              <>
                <PlatformSelector platforms={platforms} selected={selected} onToggle={(n) =>
                  setSelected(selected.includes(n) ? selected.filter((x) => x !== n) : [...selected, n])
                } />
                <button onClick={handleAdapt} disabled={loading} className={primaryBtn}>
                  {loading ? <Loader2 size={18} className="animate-spin" /> : <Sparkles size={18} />}
                  {loading ? "正在适配各平台…" : "一键适配到所选平台"}
                </button>
              </>
            )}

            {mode === "compare" && (
              <>
                <div>
                  <div className="mb-1.5 text-xs font-medium text-gray-400">选 1 个平台</div>
                  <div className="flex flex-wrap gap-2">
                    {platforms.map((p) => (
                      <button
                        key={p.name}
                        onClick={() => setComparePlatform(p.name)}
                        className={`rounded-full border px-4 py-1.5 text-sm font-medium transition-colors ${
                          comparePlatform === p.name
                            ? "border-gray-900 bg-gray-900 text-white"
                            : "border-gray-300 bg-white text-gray-600 hover:border-gray-400"
                        }`}
                      >
                        {p.display_name}
                      </button>
                    ))}
                  </div>
                </div>
                <div>
                  <div className="mb-1.5 text-xs font-medium text-gray-400">选 2+ 个模型对比</div>
                  <div className="flex flex-wrap gap-2">
                    {models.map((m) => {
                      const key = `${m.provider}:${m.model}`;
                      const on = selectedModels.includes(key);
                      return (
                        <button
                          key={key}
                          onClick={() =>
                            setSelectedModels(
                              on ? selectedModels.filter((x) => x !== key) : [...selectedModels, key]
                            )
                          }
                          className={`rounded-lg border px-3 py-1.5 text-sm font-medium transition-colors ${
                            on
                              ? "border-indigo-500 bg-indigo-50 text-indigo-700"
                              : "border-gray-300 bg-white text-gray-600 hover:border-gray-400"
                          }`}
                        >
                          {m.label}
                        </button>
                      );
                    })}
                  </div>
                </div>
                <button onClick={handleCompare} disabled={loading} className={primaryBtn}>
                  {loading ? <Loader2 size={18} className="animate-spin" /> : <GitCompare size={18} />}
                  {loading ? "正在用各模型适配…" : "对比所选模型"}
                </button>
              </>
            )}

            {error && <div className="rounded-lg bg-red-50 px-4 py-2 text-sm text-red-600">{error}</div>}
          </section>

          {/* 右：编辑器 */}
          <section className="min-h-[460px]">
            <Editor onMarkdownChange={setBodyMd} />
          </section>
        </div>

        {/* 结果区（全宽） */}
        <div className="mt-8">
          {mode === "adapt" ? (
            <>
              <SectionTitle title="各平台预览" hint="所见即所得 · 贴进对应平台后的样子" />
              {results.length === 0 && !loading && <EmptyState text="输入内容并点击「一键适配」，看同一篇内容在各平台的原生风格" />}
              {loading && <LoadingState count={selected.length} />}
              {results.length > 0 && <PreviewPanel results={results} />}
            </>
          ) : (
            <>
              <SectionTitle title="多模型对比" hint="同一平台 · 不同模型 · 选出更合心意的版本" />
              {compareResults.length === 0 && !loading && <EmptyState text="选 1 个平台 + 2 个以上模型，点「对比所选模型」" />}
              {loading && <LoadingState count={selectedModels.length} />}
              {compareResults.length > 0 && (
                <ComparePanel variants={compareResults} preferredKey={preferredKey} onPick={pickModel} />
              )}
            </>
          )}
        </div>
      </main>
    </div>
  );
}

const primaryBtn =
  "flex items-center justify-center gap-2 rounded-xl bg-gray-900 py-3 font-medium text-white transition-colors hover:bg-gray-800 disabled:opacity-50";

function Header() {
  return (
    <header className="sticky top-0 z-30 border-b border-gray-200 bg-white/90 backdrop-blur">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
        <div className="flex items-center gap-2">
          <Send size={20} className="text-gray-900" />
          <span className="text-lg font-semibold">多平台内容发布工具</span>
        </div>
        <span className="hidden text-sm text-gray-400 sm:block">适配 → 预览 → 复制 → 跳转，不假装能发</span>
      </div>
    </header>
  );
}

function ModeToggle({ mode, onChange }: { mode: Mode; onChange: (m: Mode) => void }) {
  const item = (m: Mode, label: string) => (
    <button
      onClick={() => onChange(m)}
      className={`flex-1 rounded-lg py-2 text-sm font-medium transition-colors ${
        mode === m ? "bg-white text-gray-900 shadow-sm" : "text-gray-500 hover:text-gray-700"
      }`}
    >
      {label}
    </button>
  );
  return (
    <div className="flex gap-1 rounded-xl bg-gray-100 p-1">
      {item("adapt", "一键适配（多平台）")}
      {item("compare", "多模型对比")}
    </div>
  );
}

function PlatformSelector({
  platforms,
  selected,
  onToggle,
}: {
  platforms: PlatformInfo[];
  selected: string[];
  onToggle: (name: string) => void;
}) {
  return (
    <div className="flex flex-wrap gap-2">
      {platforms.map((p) => {
        const on = selected.includes(p.name);
        return (
          <button
            key={p.name}
            onClick={() => onToggle(p.name)}
            className={`rounded-full border px-4 py-1.5 text-sm font-medium transition-colors ${
              on ? "border-gray-900 bg-gray-900 text-white" : "border-gray-300 bg-white text-gray-600 hover:border-gray-400"
            }`}
          >
            {p.display_name}
          </button>
        );
      })}
    </div>
  );
}

function SectionTitle({ title, hint }: { title: string; hint: string }) {
  return (
    <div className="mb-4 flex items-baseline gap-2">
      <h2 className="text-lg font-semibold">{title}</h2>
      <span className="text-sm text-gray-400">{hint}</span>
    </div>
  );
}

function EmptyState({ text }: { text: string }) {
  return (
    <div className="flex h-[420px] flex-col items-center justify-center rounded-xl border border-dashed border-gray-300 text-center text-gray-400">
      <Sparkles size={32} className="mb-3" />
      <p className="max-w-xs text-sm">{text}</p>
    </div>
  );
}

function LoadingState({ count }: { count: number }) {
  return (
    <div className="flex gap-6 overflow-x-auto pb-4">
      {Array.from({ length: Math.max(count, 1) }).map((_, i) => (
        <div key={i} className="w-[300px] shrink-0">
          <div className="h-[600px] animate-pulse rounded-[2.4rem] border-[11px] border-gray-200 bg-gray-100" />
        </div>
      ))}
    </div>
  );
}
