# 扩展指南：如何新增一个平台

> 本文是题目原文要求的「扩展更多平台的架构设计」交付物。
> 读完本文，你可以在 **5 分钟内、约 100 行代码** 内为本工具新增一个内容平台。
> 配套架构总览见 [ARCHITECTURE.md](ARCHITECTURE.md)，设计取舍见 [复盘.md](复盘.md) D-04。

---

## 0. 核心思想：你只需描述「身份」和「风格」

本工具的编排逻辑（组装 prompt → 调 LLM → 解析 → 渲染 → 生成跳转意图）全部在抽象基类 `PlatformAdapter` 里完成。
新增平台时，**你不写任何编排代码**，只回答两个问题：

1. 这个平台是谁？（`name` / `display_name` / `editor_url`）
2. 这个平台的内容长什么样？（`style_prompt()`）

其余方法（few-shot 样本、输出 schema、排版、预览、跳转意图、坑位说明）都有可复用的默认实现，按需覆写即可。

---

## 1. PlatformAdapter 接口定义

定义在 `backend/adapters/base.py`。

### 1.1 必须提供（每个平台必然不同）

| 成员 | 类型 | 含义 |
|---|---|---|
| `name` | 类属性 `str` | 平台唯一标识，全小写，如 `"wechat"`。用于注册表 key 与 API 路由。 |
| `display_name` | 类属性 `str` | 中文显示名，如 `"公众号"`。前端展示用。 |
| `editor_url` | 类属性 `str` | 平台官方「写新内容」入口 URL。一键跳转的目标（我们只跳转，不替用户发布）。 |
| `style_prompt()` | 方法 → `str` | **风格适配的灵魂**。描述该平台的语气、标题习惯、段落结构、互动话术。 |

### 1.2 可选覆写（有可复用默认实现）

| 方法 | 默认行为 | 何时覆写 |
|---|---|---|
| `few_shot()` | 返回 `[]` | 想用少量原创示范片段增强风格时（注意：不放真实平台内容，见 D-06）。 |
| `output_schema()` | 通用 `{title, content, summary, hashtags}` | 平台需要额外字段时（如小红书的 `cover_alt`）。 |
| `format_content(adapted)` | 拼接 标题 + 正文 + `#标签` | 平台有特殊粘贴排版时（如标签位置、纯文本约束）。 |
| `preview_template()` | `"generic"` | 想让前端用该平台专属预览外观时（PR12 的 CSS 模板 key）。 |
| `publish_intent(adapted)` | `{clipboard: format_content(...), url: editor_url}` | 极少需要；除非跳转 URL 要带动态参数。 |
| `extension_guide()` | `""` | 强烈建议填：记录该平台坑位（字符限制、标签支持、配图要求）。 |
| `strategy_profile()` | 通用档案 | 发布策略 Agent 据此判断"该不该发本平台"。**强烈建议填**：内容类型 / 长度甜区 / 调性。写了就自动进入"该发哪些平台"的打分，无需改 Agent。 |
| `ideas_schema()` | `{titles, hashtags, cover_copy}` | 平台创意需要额外字段时覆写。 |
| `generate_ideas()` | 基类按 `style_prompt` 产出标题/标签/封面文案 | 极少需要覆写；除非该平台创意逻辑特殊。 |

### 1.3 你几乎不用碰的模板方法

| 方法 | 说明 |
|---|---|
| `adapt(content, provider)` | 基类已实现：组装 `system(style_prompt) + few_shot + user(原文+schema)` → `provider.chat_json` → 收敛成 `AdaptedResult`。**子类一般不覆写。** |

---

## 2. 新平台开发的 4 步流程

```
实现  →  注册  →  测试  →  上线
```

1. **实现**：在 `backend/adapters/` 下新建 `<平台>.py`，写一个继承 `PlatformAdapter` 的类。
2. **注册**：给类加 `@register` 装饰器；并在 `backend/adapters/__init__.py` 追加一行 `from adapters import <平台>`（触发自注册）。
3. **测试**：新建 `backend/tests/test_<平台>.py`，调用统一契约 `run_contract(你的Adapter())`。
4. **上线**：跑 `pytest` 全绿后提 PR、合并。API（`/platforms`、`/adapt`）与前端预览会**自动**发现新平台，无需改动核心代码。

---

## 3. 完整示例：从零实现虚构平台 `ExamplePlatform`

假设我们要接入一个虚构平台「示例号」：风格是「极简、一句话一段、结尾带一个金句」。

### 3.1 实现 `backend/adapters/example_platform.py`

```python
"""示例平台适配器（扩展指南演示用）。"""

from __future__ import annotations

from adapters.base import PlatformAdapter, register


@register
class ExamplePlatformAdapter(PlatformAdapter):
    # --- 1) 身份：必填 ---
    name = "example"
    display_name = "示例号"
    editor_url = "https://example.com/new-post"

    # --- 2) 风格：必填 ---
    def style_prompt(self) -> str:
        return (
            "你是「示例号」的资深编辑，风格极简。\n"
            "规则：1) 每段只有一句话；2) 用词克制不浮夸；"
            "3) 结尾用一句独立成段的金句收束全文。\n"
            "保持原文事实，只改写风格。"
        )

    # --- 3) 可选：记录坑位（强烈建议填） ---
    def extension_guide(self) -> str:
        return "示例号坑位：正文上限 2000 字；不支持图片；标题需含一个动词。"
```

就这些。**约 25 行**，没有一行编排或 HTTP 代码。

### 3.2 注册（在 `backend/adapters/__init__.py` 追加一行）

```python
from adapters import example_platform  # noqa: F401  示例号
```

### 3.3 测试 `backend/tests/test_example_platform.py`

```python
import os
import pytest

from adapters.base import get_adapter
from adapters.example_platform import ExamplePlatformAdapter
from tests.adapter_contract import SAMPLE, run_contract


def test_example_contract():
    # 统一契约：身份字段齐全、style_prompt 非空、adapt 产出合法、publish_intent 含跳转
    run_contract(ExamplePlatformAdapter())


def test_example_registered():
    assert get_adapter("example").display_name == "示例号"


@pytest.mark.skipif(not os.getenv("DEEPSEEK_API_KEY"), reason="无 key 跳过 live")
def test_example_live():
    from app.llm_provider import get_provider
    result = ExamplePlatformAdapter().adapt(SAMPLE, get_provider("deepseek"))
    assert result.platform == "example" and result.content
```

### 3.4 上线

```bash
cd backend && python -m pytest -q      # 全绿
# 提交 PR、合并；/platforms 接口与前端预览自动出现「示例号」
```

---

## 4. 测试用例模板（统一契约）

所有平台共用 `backend/tests/adapter_contract.py` 里的 `run_contract(adapter)`，它断言：

- 身份字段齐全：`name` / `display_name` 非空，`editor_url` 是合法 URL；
- `style_prompt()` 非空；
- `adapt(SAMPLE, FakeProvider)` 返回合法 `AdaptedResult`（不打网络，用假 provider）；
- `adapt` 过程把 `style_prompt` 放进了 system 消息；
- `publish_intent()` 返回含非空 `clipboard` + 合法跳转 `url`。

`FakeProvider` 让契约测试**离线可跑**（CI 无需 LLM key）；真实风格效果用带 `@pytest.mark.skipif` 的 live 测试在本地验证。

---

## 5. 常见坑（跨平台差异速查）

| 维度 | 公众号 | 知乎 | B站 | 小红书 |
|---|---|---|---|---|
| 富文本/Markdown | 部分 HTML 标签被过滤 | 支持 MD，公式渲染有差异 | 支持有限，建议富文本 | **仅纯文本 + emoji** |
| emoji | 克制（≤3） | 几乎不用 | 适度点缀 | 密集（核心风格） |
| 图片 | 需先上传素材库 | 支持 | 支持 | **必须至少 1 张才能发** |
| 标签 | 无原生话题 | 话题有限 | 分区/标签 | 话题标签放正文末，>10 限流 |
| 标题字数 | 64 上限（22 内更佳） | 较宽松 | 40 内 | 20 内 |
| 外链 | 受限 | **降权** | 受限 | 受限 |

**写 `style_prompt` 的经验**：
1. 规则要**具体可执行**（"段落 2-4 句"好过"段落要短"）。
2. 给出**标题句式**示例，比抽象描述更稳。
3. 明确**互动话术**（三连 / 评论区扣 1 / 在看），这是平台辨识度的高频信号。
4. 始终加一句「保持原文事实，不要编造数据」——降低 LLM 幻觉（实测仍可能轻微补充，见复盘 5.4）。
5. 需要话题标签的平台，在 prompt 里明确**数量范围**并要求放进 `hashtags`。

---

## 6. 为什么这套架构能「5 行注册」

- **关注点分离**：编排在基类，差异在子类。新平台的认知负担只有「身份 + 风格」。
- **约定优于配置**：`@register` + `__init__` 一行导入即自动接入 API 与前端，核心代码零改动。
- **统一契约兜底**：`run_contract` 保证任何新 adapter 都满足系统其余部分的假设，重构基类时也能一键回归全部平台。

这正是题目原文「扩展更多平台的架构设计」的工程兑现。
