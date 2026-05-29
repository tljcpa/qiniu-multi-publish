"""LLM Provider 抽象层。

屏蔽不同 LLM 后端的差异，给上层（Platform Adapter）提供统一调用接口。
DeepSeek 与 Azure OpenAI 都兼容 OpenAI SDK，因此共享一个基类，子类只负责构造 client。
设计取舍见 docs/复盘.md D-12。
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Iterator

from openai import OpenAI

from app.config import settings


class LLMError(RuntimeError):
    """LLM 调用相关的错误（配置缺失、JSON 解析失败等）。"""


# 一条对话消息的类型，等价于 [{"role": "system"/"user"/"assistant", "content": "..."}]
Message = dict


class LLMProvider(ABC):
    """LLM 后端统一接口。

    上层只依赖这个抽象，不关心底层是 DeepSeek 还是 Azure。
    """

    # 后端名称（"deepseek" / "azure"），用于日志与多模型对比标注
    name: str

    @abstractmethod
    def chat(self, messages: list[Message], *, temperature: float = 0.7,
             max_tokens: int | None = None) -> str:
        """一次非流式对话，返回完整文本。"""
        raise NotImplementedError

    @abstractmethod
    def chat_stream(self, messages: list[Message], *,
                    temperature: float = 0.7) -> Iterator[str]:
        """流式对话，逐段 yield 文本增量（给前端打字机效果）。"""
        raise NotImplementedError

    @abstractmethod
    def chat_json(self, messages: list[Message], *, temperature: float = 0.7,
                  max_retries: int = 2) -> dict:
        """JSON mode 对话，返回解析后的 dict；解析失败时重试。"""
        raise NotImplementedError


class _OpenAICompatProvider(LLMProvider):
    """OpenAI 兼容协议的通用实现。

    DeepSeek 与 Azure 都走 chat.completions 接口，差异只在 client 构造，
    所以把三个能力（chat / chat_stream / chat_json）收敛在这里。
    """

    def __init__(self, client: OpenAI, model: str, name: str):
        # 注入式构造：把 client 作为参数传入，便于单元测试用 fake client 替换、不打网络
        self._client = client
        self._model = model
        self.name = name

    def chat(self, messages, *, temperature=0.7, max_tokens=None):
        resp = self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content

    def chat_stream(self, messages, *, temperature=0.7):
        stream = self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=temperature,
            stream=True,
        )
        for chunk in stream:
            # 末尾 chunk 的 delta.content 可能为 None，需过滤
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    def chat_json(self, messages, *, temperature=0.7, max_retries=2):
        # DeepSeek/OpenAI 的 JSON mode 要求 prompt 中出现 "json" 字样，否则后端报错。
        # 这里做一道保险：若所有消息里都没有 json 关键词，追加一条系统提示。
        if not _mentions_json(messages):
            messages = messages + [{
                "role": "system",
                "content": "严格只输出一个合法的 JSON 对象，不要任何额外文字或 markdown 代码块。",
            }]

        last_err: Exception | None = None
        # 首次 + max_retries 次重试
        for attempt in range(max_retries + 1):
            resp = self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=temperature,
                response_format={"type": "json_object"},
            )
            content = resp.choices[0].message.content
            try:
                return json.loads(content)
            except (json.JSONDecodeError, TypeError) as exc:
                # 解析失败：记录错误，进入下一次重试
                last_err = exc
                continue
        raise LLMError(f"chat_json 在 {max_retries + 1} 次尝试后仍无法解析为 JSON: {last_err}")


def _mentions_json(messages: list[Message]) -> bool:
    """检查消息里是否提到 json（用于 JSON mode 的前置条件）。"""
    for msg in messages:
        content = msg.get("content", "")
        if isinstance(content, str) and "json" in content.lower():
            return True
    return False


class DeepSeekProvider(_OpenAICompatProvider):
    """DeepSeek 后端（默认，便宜快）。"""

    def __init__(self, model: str | None = None):
        if not settings.deepseek_api_key:
            raise LLMError("DEEPSEEK_API_KEY 未配置，无法初始化 DeepSeekProvider")
        client = OpenAI(
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
        )
        # model 为空则用配置默认（deepseek-chat）；可传 deepseek-reasoner 做风格对比
        super().__init__(client, model or settings.deepseek_model, "deepseek")


class AzureProvider(_OpenAICompatProvider):
    """Azure OpenAI 后端（备用，用于多模型对比亮点）。"""

    def __init__(self, model: str | None = None):
        # 统一用 model 参数（对 Azure 即 deployment 名），与 get_provider(name, model=...) 一致
        if not settings.azure_openai_api_key or not settings.azure_openai_endpoint:
            raise LLMError("AZURE_OPENAI_* 未配置，无法初始化 AzureProvider")
        # 延迟导入：未配置 Azure 时不强制依赖该符号
        from openai import AzureOpenAI

        client = AzureOpenAI(
            api_key=settings.azure_openai_api_key,
            azure_endpoint=settings.azure_openai_endpoint,
            api_version=settings.azure_openai_api_version,
        )
        # Azure 用 deployment 名而非模型名，默认读配置
        super().__init__(client, model or settings.azure_openai_deployment, "azure")


def get_provider(name: str = "deepseek", **kwargs) -> LLMProvider:
    """工厂：按名称返回 LLM 后端实例。

    上层（adapter / 路由）通过这个函数拿 provider，不直接 new 子类，
    便于后续按请求参数或用户偏好切换后端。
    """
    if name == "deepseek":
        return DeepSeekProvider(**kwargs)
    if name == "azure":
        return AzureProvider(**kwargs)
    raise LLMError(f"未知 LLM 后端: {name}")
