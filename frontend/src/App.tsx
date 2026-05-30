import { useEffect, useState, type ReactNode } from "react";
import { Loader2, ArrowRight, GitCompare } from "lucide-react";
import Editor from "./components/Editor";
import PreviewPanel from "./components/PreviewPanel";
import ComparePanel from "./components/ComparePanel";
import StrategyPanel from "./components/StrategyPanel";
import {
  adaptStream,
  compareModels,
  fetchIdeas,
  fetchModels,
  fetchPlatforms,
  fetchStrategy,
  type CompareVariantResult,
  type IdeasResult,
  type ModelOption,
  type PlatformInfo,
  type PlatformResult,
  type PlatformScore,
} from "./lib/api";
import { getPreferredModel, setPreferredModel } from "./lib/preferences";

type Mode = "adapt" | "compare" | "strategy";
type IdeasState = IdeasResult | "loading" | undefined;

// 真实示例文章（demo 一键灌入，杜绝占位文案）
const SAMPLE = {
  title: "远程办公真的更高效吗",
  tags: "远程办公, 效率, 团队管理",
  body:
    "远程办公在过去几年成为很多公司的常态。它真的让人更高效吗？\n\n" +
    "## 节省了通勤，却增加了沟通成本\n\n" +
    "远程办公省去了通勤时间，安排也更灵活。但与此同时，沟通成本在上升：消息回复延迟、会议难协调、信息容易在传递中失真。\n\n" +
    "## 关键在异步协作与文档文化\n\n" +
    "真正决定远程效率的不是工具，而是习惯：把决策和流程写成文档，减少重复确认；用异步方式同步信息，避免实时打扰。\n\n" +
    "当团队建立起清晰的文档与协作规范，远程办公才能真正发挥优势。",
};

export default function App() {
  const [title, setTitle] = useState("");
  const [tagsInput, setTagsInput] = useState("");
  const [bodyMd, setBodyMd] = useState("");
  const [seed, setSeed] = useState({ markdown: "", nonce: 0 });

  const [platforms, setPlatforms] = useState<PlatformInfo[]>([]);
  const [models, setModels] = useState<ModelOption[]>([]);

  const [mode, setMode] = useState<Mode>("adapt");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [selected, setSelected] = useState<string[]>([]);
  const [results, setResults] = useState<PlatformResult[]>([]);

  const [comparePlatform, setComparePlatform] = useState("");
  const [selectedModels, setSelectedModels] = useState<string[]>([]);
  const [compareResults, setCompareResults] = useState<CompareVariantResult[]>([]);
  const [preferredKey, setPreferredKey] = useState<string | null>(null);

  // strategy 模式
  const [scores, setScores] = useState<PlatformScore[]>([]);
  const [ideasMap, setIdeasMap] = useState<Record<string, IdeasState>>({});

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
        setSelectedModels(list.slice(0, 2).map((m) => `${m.provider}:${m.model}`));
      })
      .catch((e) => setError(String(e)));
  }, []);

  useEffect(() => {
    if (!comparePlatform) {
      return;
    }
    const pref = getPreferredModel(comparePlatform);
    setPreferredKey(pref ? `${pref.provider}:${pref.model}` : null);
  }, [comparePlatform]);

  function loadSample() {
    setTitle(SAMPLE.title);
    setTagsInput(SAMPLE.tags);
    setSeed({ markdown: SAMPLE.body, nonce: seed.nonce + 1 });
  }

  function buildContent() {
    const tags = tagsInput.split(/[,，\s]+/).map((t) => t.trim()).filter(Boolean);
    return { title, body_md: bodyMd, tags };
  }

  function ensureInput(): boolean {
    setError(null);
    if (!title.trim() && !bodyMd.trim()) {
      setError("请先输入标题或正文，或点「载入示例」");
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
    const acc: Record<string, PlatformResult> = {};
    const startAt: Record<string, number> = {};
    const order: string[] = [];
    const flush = () => setResults(order.map((p) => acc[p]));
    try {
      await adaptStream(
        { content: buildContent(), platforms: selected },
        {
          onMeta: (platform, displayName, previewTemplate) => {
            acc[platform] = {
              platform, display_name: displayName, title: "", content: "", summary: "",
              hashtags: [], model: "", preview_template: previewTemplate, formatted: "",
              publish_intent: null, error: null, streaming: true,
            };
            startAt[platform] = performance.now();
            order.push(platform);
            flush();
          },
          onDelta: (platform, text) => {
            const cur = acc[platform];
            if (cur) {
              acc[platform] = { ...cur, content: cur.content + text };
              flush();
            }
          },
          onDone: (platform, result) => {
            const elapsed = startAt[platform] ? Math.round(performance.now() - startAt[platform]) : undefined;
            acc[platform] = { ...result, streaming: false, elapsed_ms: elapsed };
            flush();
          },
          onError: (platform, err) => {
            const cur = acc[platform];
            acc[platform] = { ...(cur ?? ({} as PlatformResult)), platform, error: err, streaming: false };
            flush();
          },
        }
      );
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

  async function handleStrategy() {
    if (!ensureInput()) {
      return;
    }
    setLoading(true);
    setScores([]);
    setIdeasMap({});
    try {
      setScores(await fetchStrategy(buildContent()));
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }

  async function handleGenerateIdeas(platform: string) {
    setIdeasMap((m) => ({ ...m, [platform]: "loading" }));
    try {
      const r = await fetchIdeas(buildContent(), platform);
      setIdeasMap((m) => ({ ...m, [platform]: r }));
    } catch (e) {
      setIdeasMap((m) => ({
        ...m,
        [platform]: { platform, display_name: platform, titles: [], hashtags: [], cover_copy: [], model: "", error: String(e) },
      }));
    }
  }

  const charCount = bodyMd.length;

  return (
    <div className="min-h-screen bg-ink-900 text-paper">
      <TopBar />
      <main className="mx-auto max-w-[1280px] px-5 py-5">
        <div className="grid grid-cols-1 gap-5 lg:grid-cols-[minmax(0,380px)_minmax(0,1fr)]">
          {/* 左：控制台 */}
          <section className="flex flex-col gap-4">
            <Panel>
              <div className="flex items-center justify-between">
                <Eyebrow>原始内容</Eyebrow>
                <button
                  onClick={loadSample}
                  className="rounded border border-ink-600 px-2 py-0.5 font-mono text-[11px] text-paper-dim transition-colors hover:text-paper"
                >
                  载入示例
                </button>
              </div>
              <input
                className="mt-2 w-full bg-transparent font-serif text-xl font-semibold text-paper placeholder-paper-faint focus:outline-none"
                placeholder="标题"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
              />
              <input
                className="mt-1.5 w-full bg-transparent font-mono text-[13px] text-paper-dim placeholder-paper-faint focus:outline-none"
                placeholder="标签，逗号分隔"
                value={tagsInput}
                onChange={(e) => setTagsInput(e.target.value)}
              />
            </Panel>

            <ModeToggle mode={mode} onChange={setMode} />

            {mode === "adapt" && (
              <>
                <div>
                  <Eyebrow>目标平台</Eyebrow>
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {platforms.map((p) => (
                      <Chip
                        key={p.name}
                        on={selected.includes(p.name)}
                        onClick={() =>
                          setSelected(selected.includes(p.name) ? selected.filter((x) => x !== p.name) : [...selected, p.name])
                        }
                      >
                        {p.display_name}
                      </Chip>
                    ))}
                  </div>
                </div>
                <PrimaryButton onClick={handleAdapt} loading={loading}>
                  {loading ? "适配中…" : <>一键适配 <ArrowRight size={15} /></>}
                </PrimaryButton>
              </>
            )}
            {mode === "strategy" && (
              <>
                <p className="text-[13px] leading-relaxed text-paper-dim">
                  策略 Agent 会判断这篇内容更适合发到哪些平台，并按需为平台生成原生标题、话题标签与封面文案。
                </p>
                <PrimaryButton onClick={handleStrategy} loading={loading}>
                  {loading ? "分析中…" : <>分析发布策略 <ArrowRight size={15} /></>}
                </PrimaryButton>
              </>
            )}
            {mode === "compare" && (
              <>
                <div>
                  <Eyebrow>平台（单选）</Eyebrow>
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {platforms.map((p) => (
                      <Chip key={p.name} on={comparePlatform === p.name} onClick={() => setComparePlatform(p.name)}>
                        {p.display_name}
                      </Chip>
                    ))}
                  </div>
                </div>
                <div>
                  <Eyebrow>模型（多选对比）</Eyebrow>
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {models.map((m) => {
                      const key = `${m.provider}:${m.model}`;
                      return (
                        <Chip
                          key={key}
                          on={selectedModels.includes(key)}
                          onClick={() =>
                            setSelectedModels(
                              selectedModels.includes(key) ? selectedModels.filter((x) => x !== key) : [...selectedModels, key]
                            )
                          }
                        >
                          {m.label}
                        </Chip>
                      );
                    })}
                  </div>
                </div>
                <PrimaryButton onClick={handleCompare} loading={loading}>
                  {loading ? "对比中…" : <>对比所选模型 <GitCompare size={15} /></>}
                </PrimaryButton>
              </>
            )}

            {error && <div className="rounded border border-red-900/60 bg-red-950/40 px-3 py-2 text-sm text-red-300">{error}</div>}
          </section>

          {/* 右：编辑器 */}
          <section className="flex min-h-[440px] flex-col">
            <div className="mb-2 flex items-center justify-between">
              <Eyebrow>编辑器</Eyebrow>
              <span className="font-mono text-[11px] text-paper-faint">{charCount} 字</span>
            </div>
            <div className="min-h-0 flex-1">
              <Editor onMarkdownChange={setBodyMd} seed={seed} />
            </div>
          </section>
        </div>

        {/* 结果区 */}
        <div className="mt-7 border-t border-ink-700 pt-6">
          {mode === "adapt" && (
            <>
              <ResultsHeader title="平台预览" results={results} />
              {results.length === 0 && !loading && <EmptyState text="点「载入示例」或自己写一篇，再「一键适配」。同一篇内容会被改写成各平台的原生风格并逐字预览。" />}
              {loading && results.length === 0 && <SkeletonRow count={selected.length} />}
              {results.length > 0 && <PreviewPanel results={results} />}
            </>
          )}
          {mode === "compare" && (
            <>
              <CompareHeader platform={comparePlatform} platforms={platforms} count={compareResults.length} />
              {compareResults.length === 0 && !loading && <EmptyState text="选 1 个平台与 2 个以上模型，对比同一篇内容在不同模型下的适配效果与耗时。" />}
              {loading && <SkeletonRow count={selectedModels.length} />}
              {compareResults.length > 0 && <ComparePanel variants={compareResults} preferredKey={preferredKey} onPick={pickModel} />}
            </>
          )}
          {mode === "strategy" && (
            <>
              <div className="mb-4 flex items-baseline justify-between">
                <h2 className="font-serif text-[18px] font-semibold text-paper">发布策略</h2>
                <span className="font-mono text-[11px] text-paper-faint">{scores.length > 0 ? "按契合度排序" : "该发哪些平台 · 原生创意"}</span>
              </div>
              {scores.length === 0 && !loading && <EmptyState text="写一篇内容，点「分析发布策略」。Agent 会判断它更适合发到哪些平台，并按需生成原生标题/话题标签/封面文案。" />}
              {loading && scores.length === 0 && (
                <div className="flex items-center gap-2 text-sm text-paper-faint">
                  <Loader2 size={15} className="animate-spin" /> 策略分析中…
                </div>
              )}
              {scores.length > 0 && <StrategyPanel scores={scores} ideas={ideasMap} onGenerate={handleGenerateIdeas} />}
            </>
          )}
        </div>
      </main>
    </div>
  );
}

function TopBar() {
  return (
    <header className="sticky top-0 z-30 border-b border-ink-700 bg-ink-950">
      <div className="mx-auto flex max-w-[1280px] items-center justify-between px-5 py-2.5">
        <div className="flex items-center gap-2.5">
          <span className="h-3.5 w-3.5 rounded-[2px] bg-clay" />
          <span className="font-serif text-[17px] font-semibold text-paper">多平台内容发布工具</span>
          <span className="hidden font-mono text-[11px] text-paper-faint sm:inline">multi-publish</span>
        </div>
        <span className="hidden font-mono text-[11px] text-paper-dim md:inline">适配 → 预览 → 复制 → 跳转 · 不假装能发</span>
      </div>
    </header>
  );
}

function Panel({ children }: { children: ReactNode }) {
  return <div className="rounded-md border border-ink-700 bg-ink-850 p-3.5">{children}</div>;
}

function Eyebrow({ children }: { children: ReactNode }) {
  return <div className="text-[11px] font-medium tracking-[0.08em] text-paper-faint">{children}</div>;
}

function ModeToggle({ mode, onChange }: { mode: Mode; onChange: (m: Mode) => void }) {
  const item = (m: Mode, label: string) => (
    <button
      onClick={() => onChange(m)}
      className={`flex-1 rounded py-1.5 text-[13px] font-medium transition-colors ${
        mode === m ? "bg-ink-700 text-paper" : "text-paper-dim hover:text-paper"
      }`}
    >
      {label}
    </button>
  );
  return (
    <div className="flex gap-1 rounded-md border border-ink-700 bg-ink-850 p-1">
      {item("adapt", "一键适配")}
      {item("strategy", "发布策略")}
      {item("compare", "多模型对比")}
    </div>
  );
}

function Chip({ children, on, onClick }: { children: ReactNode; on: boolean; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className={`rounded border px-3 py-1 text-[13px] font-medium transition-colors ${
        on
          ? "border-clay bg-clay-soft text-clay"
          : "border-ink-700 bg-ink-850 text-paper-dim hover:border-ink-600 hover:text-paper"
      }`}
    >
      {children}
    </button>
  );
}

function PrimaryButton({ children, onClick, loading }: { children: ReactNode; onClick: () => void; loading: boolean }) {
  return (
    <button
      onClick={onClick}
      disabled={loading}
      className="flex items-center justify-center gap-1.5 rounded bg-clay py-2.5 text-[14px] font-semibold text-white transition-colors hover:bg-clay-hover disabled:opacity-60"
    >
      {loading && <Loader2 size={15} className="animate-spin" />}
      {children}
    </button>
  );
}

function ResultsHeader({ title, results }: { title: string; results: PlatformResult[] }) {
  const done = results.filter((r) => !r.streaming && !r.error).length;
  return (
    <div className="mb-4 flex items-baseline justify-between">
      <h2 className="font-serif text-[18px] font-semibold text-paper">{title}</h2>
      {results.length > 0 && (
        <span className="font-mono text-[11px] text-paper-faint">
          {done}/{results.length} 完成 · 流式 SSE
        </span>
      )}
    </div>
  );
}

function CompareHeader({ platform, platforms, count }: { platform: string; platforms: PlatformInfo[]; count: number }) {
  const name = platforms.find((p) => p.name === platform)?.display_name ?? platform;
  return (
    <div className="mb-4 flex items-baseline justify-between">
      <h2 className="font-serif text-[18px] font-semibold text-paper">多模型对比</h2>
      <span className="font-mono text-[11px] text-paper-faint">{count > 0 ? `${name} · ${count} 个模型` : "同一平台 · 不同模型"}</span>
    </div>
  );
}

function EmptyState({ text }: { text: string }) {
  return (
    <div className="flex h-[360px] items-center justify-center rounded-md border border-dashed border-ink-700">
      <p className="max-w-sm px-6 text-center text-[13px] leading-relaxed text-paper-dim">{text}</p>
    </div>
  );
}

function SkeletonRow({ count }: { count: number }) {
  return (
    <div className="flex gap-5 overflow-x-auto pb-4">
      {Array.from({ length: Math.max(count, 1) }).map((_, i) => (
        <div key={i} className="w-[300px] shrink-0">
          <div className="h-[600px] animate-pulse rounded-[2.4rem] border-[11px] border-ink-800 bg-ink-850" />
        </div>
      ))}
    </div>
  );
}
