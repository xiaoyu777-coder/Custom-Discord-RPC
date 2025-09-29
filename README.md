# Custom-Discord-RPC

一个用 PyQt5 编写的桌面 GUI 工具，用于编辑并将 Rich Presence 发布到本地运行的 Discord 客户端。

## 主要特性

- 编辑 details / state、large/small image keys 与对应文本。
- large/small image 支持占位符（placeholder）：如果输入框为空，发布时将使用占位 key。
- 主题切换：支持暗色和浅色主题。
- 配置保存/加载到 `presence_config.json`

## 运行

- 1.建议创建并激活虚拟环境。
- 2.安装依赖：

   ```
   pip install PyQt5 pypresence
   ```

- 3.启动程序：

   ```
   python Custom-Discord-RPC.py
   ```

## 注意

- 要把状态实际显示到 Discord 上，你必须在 `https://discord.com/developers/applications` 创建应用并使用对应的 `client_id`。
- 本项目仅包含客户端发布逻辑，不会替你注册或伪装成别人的应用。

**MADE BY GITHUB COPILOT**

**NO LICENSE**