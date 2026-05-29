# 多平台内容发布工具

> 一份内容，自动适配公众号 / 知乎 / B 站 / 小红书的格式**与风格**——
> 适配 → 预览 → 一键复制 → 跳转，**不假装能发**。

> 七牛云 × XEngineer 暑期实训营 · 题目二作品

- **在线试用（已上线）**：https://publish.qiniu.zdwktlj.top
- **演示视频（47 秒）**：[在线观看](https://publish.qiniu.zdwktlj.top/demo/multi-publish-demo.mp4)（自托管录屏，含旁白）
- 架构文档：[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) · 扩展指南：[docs/EXTENSION_GUIDE.md](docs/EXTENSION_GUIDE.md) · 部署文档：[docs/DEPLOY.md](docs/DEPLOY.md)

---

## 演示视频

**▶ [在线演示视频（47 秒）](https://publish.qiniu.zdwktlj.top/demo/multi-publish-demo.mp4)** — 自托管录屏，含旁白。

完整走通核心闭环：载入内容 → 一键适配 4 平台 → 高保真手机壳预览 → 「复制并前往知乎发布」。讲解脚本见 [docs/答辩.md](docs/答辩.md)。

## 我们的产品决策：为什么不做"真发布"

公众号发布需订阅号/服务号资质 + 微信审核；知乎、B 站、小红书**没有公开的内容发布 API**。
市面"发布工具"靠浏览器自动化 / RPA，法律灰色且不可靠。

所以我们诚实地不假装能发。我们做的是 **内容适配 → 平台预览 → 一键复制到剪贴板 → 跳转平台官方编辑页**。
真正"按下发布"那一步，永远留在用户手里、平台官方界面里——这是对创作者隐私与平台规则的尊重。

价值：把"同一篇文章发到 4 个平台"从 ~30 分钟降到 ~3 分钟。

## 核心特性

- **Platform Adapter 插件化架构**：新增一个平台 = 实现一个 Adapter 类 + 注册，约一个文件（详见扩展指南）
- **4 大平台原生风格适配**：不只是 markdown→html，是公众号正式 / 知乎严谨 / B 站口语 / 小红书种草的**风格**本地化
- **所见即所得平台预览**：每个平台用高保真"手机壳"模拟其真实展示外观
- **流式打字机**：一键适配时 4 个平台并发逐字生成（SSE），边出边看
- **一键复制 + 跳转闭环**：复制适配后内容到剪贴板，并新标签打开对应平台编辑页
- **多模型对比**：同一平台用 DeepSeek vs Azure GPT-4.1-mini 分别适配、并排比耗时与效果，选定模型记忆为该平台偏好

## 效果示例

同一篇《远程办公真的更高效吗》原文，一键适配到 4 个平台，标题风格截然不同：

| 平台 | 适配后标题 |
|---|---|
| 公众号 | 远程办公效率低？关键在这两点 |
| 知乎 | 远程办公真的更高效吗？关键在异步协作与文档文化 |
| B站 | 远程办公真的更高效？我愿称之为"血赚"还是"血亏" |
| 小红书 | ❌别再被忽悠了！远程办公的真相是…… |

正文同样会被改写成各平台原生风格（段落长度、emoji 密度、互动话术、话题标签），并以真机样式预览。

## 技术栈

| 层 | 选型 |
|---|---|
| 后端 | Python 3.11 + FastAPI |
| LLM | DeepSeek（OpenAI 兼容协议），Azure OpenAI 备用 |
| 前端 | React + Vite + Tailwind + shadcn/ui，Tiptap 富文本 |
| 数据库 | SQLite |
| 部署 | Docker Compose + Caddy（自动 HTTPS） |

## 快速开始

```bash
# 后端
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # 填入 DEEPSEEK_API_KEY
uvicorn app.main:app --reload --port 8082
# 访问 http://127.0.0.1:8082/health 应返回 {"status":"ok"}
```

```bash
# 前端（在内存充足的机器上）
cd frontend
npm install
npm run dev          # 开发，自动代理 /adapt /platforms 等到本地 8082
# 或 npm run build 产出 dist/ 交由 Caddy/静态服务器托管
```

完整部署（Docker 后端 + Caddy 自动 HTTPS + 多项目隔离）见 [docs/DEPLOY.md](docs/DEPLOY.md)。

## 系统架构

完整架构图与说明见 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)（PR2 交付）。

## 扩展新平台

```python
from adapters.base import PlatformAdapter, register

@register
class MyPlatformAdapter(PlatformAdapter):
    name = "my-platform"
    # 实现 style_prompt / format_content / preview_template / publish_intent ...
```

完整指南：[docs/EXTENSION_GUIDE.md](docs/EXTENSION_GUIDE.md)（PR9 交付）。

## 项目状态

本仓库在 72 小时实战周期内（2026-05-29 ~ 05-31）按 PR 工作流持续开发，
每个 PR 只做一件事，主分支始终保持可运行。核心功能与差异化亮点（含多模型对比、流式适配）均已上线，
后端含离线单测 + 真实 LLM 联调。设计决策日志见 [docs/复盘.md](docs/复盘.md)，答辩脚本见 [docs/答辩.md](docs/答辩.md)。

## 第三方依赖与原创声明

本项目仅使用以下开源库的公开 API，**未复制任何第三方项目的源码**：

- 后端：FastAPI、Uvicorn、Pydantic / pydantic-settings、openai-python（用于调用 DeepSeek/Azure 的 OpenAI 兼容接口）、pytest、httpx
- 前端：React、Vite、TypeScript、Tailwind CSS、Tiptap（含 tiptap-markdown）、marked、DOMPurify、lucide-react、IBM Plex 字体
- 部署：Docker、Caddy

**原创部分（本项目自有代码与设计）**：
- Platform Adapter 插件化架构（抽象基类、注册表、统一契约测试模板）与公众号/知乎/B站/小红书四个具体 adapter
- 各平台风格适配 prompt（自行总结的风格规则，不抄平台真实内容）
- LLMProvider 双后端抽象、FastAPI 路由（适配/流式 SSE/多模型对比）
- 全部前端组件（编辑器集成、高保真手机壳预览、复制跳转、对比面板）与视觉设计
- 全部文档（架构、扩展指南、部署、复盘、答辩脚本）

以上原创代码均为本批次（2026-05-29 起）新写，无复用作者过去项目的代码。

## AI 协作声明

本项目通过 Claude Code（AI 编程助手）辅助开发：AI 参与了框架代码起草、风格 prompt 调试、前端组件与样式实现；
关键决策（产品定位、Adapter 接口最小集、设计语言等）由人确定，代码经过人工审阅、测试与定型。
完整的 Prompt / 决策 / AI 出错与修正记录见 [docs/复盘.md](docs/复盘.md)。

## 开源协议

[MIT](LICENSE)

## 作者

tljcpa
