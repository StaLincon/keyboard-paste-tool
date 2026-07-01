# 键盘粘贴工具 (Keyboard Paste Tool)

一个适用于 Windows 的键盘模拟粘贴工具，通过模拟真实键盘输入解决远程 Kali 虚拟机中特殊字符转换问题。

## 功能特点

- **自定义快捷键**: 支持自定义触发热键，默认 `Ctrl+Alt+V`
- **特殊字符支持**: 正确处理 `"`, `'`, `>`, `<`, `*`, `;`, `&`, `|` 等特殊字符
- **速度可调**: 字符间延迟 1-200ms 可调节
- **首字延迟**: 输入前等待 0-2000ms，确保窗口焦点就绪后再开始输入
- **后台运行**: 系统托盘常驻，不干扰其他操作
- **防重复**: 互斥锁防止多实例运行

## 技术实现

- 使用 `SendInput` API 模拟真实键盘输入
- 特殊字符使用扫描码模式（ScanCode）确保远程桌面正确接收
- 普通字符使用 Unicode 模式提高效率

## 快速开始

### 运行已编译的程序

1. 运行 `dist/键盘粘贴工具.exe`
2. 程序自动启动并最小化到系统托盘
3. 使用 `Ctrl+C` 复制文本
4. 使用 `Ctrl+Alt+V` 在目标窗口触发模拟输入

### 从源码构建

```bash
# 安装依赖
pip install -r requirements.txt

# 运行
python main.py

# 打包为 exe
pyinstaller --onefile --noconsole --name "键盘粘贴工具" --add-data "keyboard_handler.py;." --add-data "ui.py;." --hidden-import keyboard --hidden-import pyperclip --hidden-import pystray --hidden-import PIL --hidden-import PIL.Image --hidden-import PIL.ImageDraw --hidden-import tkinter --hidden-import ctypes --hidden-import ctypes.wintypes main.py
```

## 文件结构

```
├── main.py              # 主入口，集成系统托盘
├── keyboard_handler.py  # 核心模块：热键监听 + SendInput 键盘模拟
├── ui.py                # 设置面板（tkinter）
├── requirements.txt     # 依赖列表
├── build.bat            # 一键打包脚本
└── dist/                # 打包输出目录
```

## 配置说明

| 设置项 | 默认值 | 说明 |
|--------|--------|------|
| 字符间延迟 | 5ms | 控制输入速度，建议 10-50ms |
| 首字前延迟 | 200ms | 防止切换窗口时开头字符丢失 |

## 适用场景

- 远程桌面连接到 Kali Linux
- VNC 连接到远程虚拟机
- 任何需要模拟真实键盘输入的场景

## 系统要求

- Windows 10 及以上
- Python 3.8+（开发环境）

## 许可证

MIT License