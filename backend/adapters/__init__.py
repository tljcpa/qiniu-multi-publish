"""Platform Adapter 插件化架构包。

核心抽象基类 PlatformAdapter 与注册表 PlatformRegistry 在 PR4 接入，
各平台具体 adapter（公众号 / 知乎 / B 站 / 小红书）在 PR5-PR8 接入。
设计目标：新增一个平台 = 实现一个 Adapter 类 + 注册，约 100 行一个文件。
详见 docs/EXTENSION_GUIDE.md（PR9 交付）。
"""
