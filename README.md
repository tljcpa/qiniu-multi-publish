# 多平台内容发布工具

> 一份内容，自动适配公众号 / 知乎 / B 站 / 小红书的格式**与风格**——
> 适配 → 预览 → 一键复制 → 跳转，**不假装能发**。

> 七牛云 × XEngineer 暑期实训营 · 题目二作品

- **在线试用（已上线）**：https://publish.qiniu.zdwktlj.top
- 演示视频：待录制上传（B 站）
- 架构文档：[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) · 扩展指南：[docs/EXTENSION_GUIDE.md](docs/EXTENSION_GUIDE.md) · 部署文档：[docs/DEPLOY.md](docs/DEPLOY.md)

---

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

前端与 Docker 一键启动方式随 PR11 / PR14 补充。

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
每个 PR 只做一件事，主分支始终保持可运行。设计决策日志见 [docs/复盘.md](docs/复盘.md)。

## AI 协作声明

本项目通过 Claude Code 辅助开发。Prompt / 关键决策 / review 记录见 [docs/复盘.md](docs/复盘.md)。
代码经过人工审阅、测试与定型。

## 开源协议

[MIT](LICENSE)

## 作者

tljcpa
