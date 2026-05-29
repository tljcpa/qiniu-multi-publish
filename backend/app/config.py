"""应用配置。

通过 pydantic-settings 从环境变量 / .env 文件载入配置，带类型校验。
真实密钥不入 git，通过 .env（被 .gitignore 忽略）或部署环境注入。
LLM 后端的具体接入在 PR3（llm_provider）完成，这里只占位声明字段。
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """全局配置单例。"""

    # 应用元信息
    app_name: str = "multi-publish"
    # 监听端口：与同机另外两个项目隔离，本项目固定 8082（见 BRIEF §3.4）
    port: int = 8082

    # LLM 默认后端：DeepSeek（OpenAI 兼容协议），实际调用在 PR3 接入
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"

    # 备用后端：Azure OpenAI（多模型对比用），实际调用在 PR3 接入
    azure_openai_api_key: str = ""
    azure_openai_endpoint: str = ""

    # 从 .env 读取；忽略未声明的多余变量，避免共享 shared.env 里其它项目的键报错
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


# 全局单例，应用各处 import 复用
settings = Settings()
