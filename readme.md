



# EdgeDrop

EdgeDrop 是一款专为 Windows 系统打造的极简、高效的桌面边缘文件拖拽分类工具。

它能够像系统任务栏一样“钉”在屏幕左侧，拥有独立的屏幕领地。通过极简的 JSON 配置，你可以将杂乱的文件快速拖放分发到不同的本地文件夹或 SMB 网络映射盘中，是多项目并行和资料整理的终极效率组件。

## ✨ 核心特性

* **🖥️ 系统级边缘停靠 (AppBar API)**
  应用独占屏幕左侧 10% 的空间。当你将其他应用（如浏览器、资源管理器）最大化时，它们会自动避开 EdgeDrop，永远不会发生窗口遮挡，完美融入你的双屏或单屏工作流。
* **🚀 原生传输体验 (Win32 API)**
  摒弃了常规 Python 脚本的静默文件移动，底层直接调用 Windows `SHFileOperation` API。**这意味着当你向 SMB/NAS 网络盘转移超大文件时，界面绝不会卡死**，系统会弹出你最熟悉的原生进度条，并完美处理同名文件冲突。
* **🎨 现代暗黑 UI 与交互**
  基于 PySide6 构建，采用无边框设计与深色极客风（Dark Mode）。支持拖拽悬浮高亮变色，视觉反馈清晰纯粹。
* **⚙️ JSON 动态热重载**
  分类区块由 JSON 文件驱动。不仅支持自定义区块名称、目标路径和专属高亮颜色，还支持通过界面一键切换不同的配置文件（如工作模式、个人模式），无需重启应用即可热重载界面。

## 🛠️ 快速开始

### 1. 环境依赖

确保你的系统已安装 Python 3.x。
打开终端（CMD 或 PowerShell），安装图形界面核心库 PySide6：

```bash
pip install PySide6
```

*(注：如果下载速度较慢，建议附加国内镜像源，例如 `pip install PySide6 -i https://pypi.tuna.tsinghua.edu.cn/simple`)*

### 2. 配置文件

在 `main.py` 同级目录下创建 `config.json` 文件，配置你的分类名称、目标绝对路径和悬停高亮颜色。既支持本地硬盘路径，也支持网络映射盘符：

```json
{
  "categories": {
    "项目文档": {
      "path": "D:\\Work\\Projects",
      "color": "#007ACC"
    },
    "财务报表": {
      "path": "Z:\\SMB_Share\\Finance",
      "color": "#E81123"
    },
    "素材图库": {
      "path": "E:\\Assets\\Images",
      "color": "#107C10"
    }
  }
}
```

*注意：JSON 格式中的 Windows 路径反斜杠需要使用 `\\` 进行转义。*

### 3. 运行应用

在命令行中运行以下指令启动面板：

Bash

```python
python main.py
```

**💡 沉浸式桌面体验技巧：** 在日常使用中，强烈建议将 `main.py` 的文件后缀重命名为 `main.pyw`。之后只需双击该文件即可静默启动，隐藏背后的黑色控制台窗口，获得纯粹的原生桌面软件体验。

## ⚠️ 极客避坑指南

由于本应用动用了底层系统接口接管了 Windows 的屏幕空间分配（AppBar）：

1. **必须正常退出**：请务必通过点击应用右上角的 **“✕”** 按钮来退出程序，这样程序在关闭前会将屏幕空间归还给系统。
2. **异常处理**：如果在代码编辑器（如 VSCode、PyCharm）中强制终止（Kill）了该进程，系统将无法收到释放领地的信号，导致屏幕左侧留出 10% 的无法点击的空白区域。若不慎发生此情况，请按 `Ctrl+Shift+Esc` 打开任务管理器，找到 **Windows 资源管理器 (explorer.exe)** 并点击“重新启动”即可瞬间恢复。

## 🧱 技术栈

- **Python 3** - 核心逻辑
- **PySide6 (Qt for Python)** - 现代 GUI 渲染
- **ctypes** - 调用 Windows 底层 Win32 API (AppBar & SHFileOperation)

## 📄 许可证

本项目采用 [MIT License](https://www.google.com/search?q=LICENSE&authuser=1) 开源协议。