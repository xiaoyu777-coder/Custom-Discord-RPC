# Custom-Discord-RPC

这是一个用 PyQt5 编写的小工具，用于构建并（可选）发布 Discord Rich Presence 到本地 Discord 客户端。

主要特性

- 本地 GUI：编辑 details/state、image keys、image texts、是否显示开始时间。
- large/small image 支持占位符（placeholder）：如果你没有在输入框里输入任何值，发布时会使用预设的占位值。
- 主题切换：支持暗色和浅色主题。
- 可保存/加载配置到 `presence_config.json`，支持把 `client_id` 保存到 `client_id.txt` 并从中读取。
- 可选真实发布：如果安装了 `pypresence` 且提供了有效的 Discord Application Client ID（在 Developer Portal 创建），可以连接本地 Discord 并发布 Rich Presence。

运行

1. 建议创建并激活虚拟环境。
2. 安装依赖（GUI 必需）：

```powershell
pip install PyQt5
# 如果需要发布到本地 Discord 客户端，还需要:
pip install pypresence
```

3. 运行程序：

```powershell
python RPC.py
```

注意

- 要把状态实际显示到 Discord 上，你必须在 `https://discord.com/developers/applications` 创建应用并使用对应的 `client_id`。
- 本项目仅提供本地控制和发布的客户端逻辑，不会替你注册或伪装成别人的应用。

**MADE BY GITHUB COPILOT**
**NO COPYRIGHT INTENTED**