"""Platform Adapter 插件化架构包。

核心抽象基类 PlatformAdapter 与注册表 PlatformRegistry 在 PR4 接入，
各平台具体 adapter（公众号 / 知乎 / B 站 / 小红书）在 PR5-PR8 接入。
设计目标：新增一个平台 = 实现一个 Adapter 类 + 注册，约 100 行一个文件。
详见 docs/EXTENSION_GUIDE.md（PR9 交付）。

下面的导入触发各平台 adapter 的自注册（import 即 @register 生效）。
新增平台时在此追加一行 import 即可被全局发现。
"""

from adapters import wechat  # noqa: F401  公众号
from adapters import zhihu  # noqa: F401  知乎
from adapters import bilibili  # noqa: F401  B站

