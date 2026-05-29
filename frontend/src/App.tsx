import { useEffect, useState } from "react";
import { Sparkles, Loader2, Send } from "lucide-react";
import Editor from "./components/Editor";
import PreviewPanel from "./components/PreviewPanel";
import {
  adaptContent,
  fetchPlatforms,
  type PlatformInfo,
  type PlatformResult,
} from "./lib/api";

export default function App() {
  const [title, setTitle] = useState("");
  const [tagsInput, setTagsInput] = useState("");
  const [bodyMd, setBodyMd] = useState("");

  const [platforms, setPlatforms] = useState<PlatformInfo[]>([]);
  const [selected, setSelected] = useState<string[]>([]);

  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<PlatformResult[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchPlatforms()
      .then((list) => {
        setPlatforms(list);
        setSelected(list.map((p) => p.name));
      })
      .catch((e) => setError(String(e)));
  }, []);

  function togglePlatform(name: string) {
    if (selected.includes(name)) {
      setSelected(selected.filter((n) => n !== name));
    } else {
      setSelected([...selected, name]);
    }
  }

  async function handleAdapt() {
    setError(null);
    if (!title.trim() && !bodyMd.trim()) {
      setError("请先输入标题或正文");
      return;
    }
    if (selected.length === 0) {
      setError("请至少选择一个平台");
      return;
    }
    setLoading(true);
    setResults([]);
    try {
      const tags = tagsInput
        .split(/[,，\s]+/)
        .map((t) => t.trim())
        .filter(Boolean);
      const res = await adaptContent({
        content: { title, body_md: bodyMd, tags },
        platforms: selected,
      });
      setResults(res);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900">
      <Header />
      <main className="mx-auto max-w-7xl px-4 py-6">
        {/* 输入区 */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
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
            <PlatformSelector platforms={platforms} selected={selected} onToggle={togglePlatform} />
            <button
              onClick={handleAdapt}
              disabled={loading}
              className="flex items-center justify-center gap-2 rounded-xl bg-gray-900 py-3 font-medium text-white transition-colors hover:bg-gray-800 disabled:opacity-50"
            >
              {loading ? <Loader2 size={18} className="animate-spin" /> : <Sparkles size={18} />}
              {loading ? "正在适配各平台…" : "一键适配到所选平台"}
            </button>
            {error && <div className="rounded-lg bg-red-50 px-4 py-2 text-sm text-red-600">{error}</div>}
          </section>

          <section className="min-h-[460px]">
            <Editor onMarkdownChange={setBodyMd} />
          </section>
        </div>

        {/* 预览区（全宽，手机壳并排） */}
        <div className="mt-8">
          <div className="mb-4 flex items-baseline gap-2">
            <h2 className="text-lg font-semibold">各平台预览</h2>
            <span className="text-sm text-gray-400">所见即所得 · 贴进对应平台后的样子</span>
          </div>
          {results.length === 0 && !loading && <EmptyState />}
          {loading && <LoadingState count={selected.length} />}
          {results.length > 0 && <PreviewPanel results={results} />}
        </div>
      </main>
    </div>
  );
}

function Header() {
  return (
    <header className="sticky top-0 z-30 border-b border-gray-200 bg-white/90 backdrop-blur">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
        <div className="flex items-center gap-2">
          <Send size={20} className="text-gray-900" />
          <span className="text-lg font-semibold">多平台内容发布工具</span>
        </div>
        <span className="hidden text-sm text-gray-400 sm:block">
          适配 → 预览 → 复制 → 跳转，不假装能发
        </span>
      </div>
    </header>
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
              on
                ? "border-gray-900 bg-gray-900 text-white"
                : "border-gray-300 bg-white text-gray-600 hover:border-gray-400"
            }`}
          >
            {p.display_name}
          </button>
        );
      })}
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex h-[420px] flex-col items-center justify-center rounded-xl border border-dashed border-gray-300 text-center text-gray-400">
      <Sparkles size={32} className="mb-3" />
      <p className="text-sm">输入内容并点击「一键适配」</p>
      <p className="mt-1 text-xs">同一篇内容会被改写成各平台的原生风格，并以真机样式预览</p>
    </div>
  );
}

function LoadingState({ count }: { count: number }) {
  return (
    <div className="flex gap-6 overflow-x-auto pb-4">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="w-[300px] shrink-0">
          <div className="h-[600px] animate-pulse rounded-[2.4rem] border-[11px] border-gray-200 bg-gray-100" />
        </div>
      ))}
    </div>
  );
}
