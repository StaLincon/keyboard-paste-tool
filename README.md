<div align="center">

# ⌨️ 键盘粘贴工具 (Keyboard Paste Tool)

**Windows 键盘模拟粘贴工具 — 解决远程 Kali 虚拟机特殊字符转换问题**

[![GitHub Stars](https://img.shields.io/github/stars/StaLincon/keyboard-paste-tool?style=flat-square)](https://github.com/StaLincon/keyboard-paste-tool/stargazers)
[![License](https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8%2B-yellow?style=flat-square)]()
[![Platform](https://img.shields.io/badge/platform-Windows-0078D6?style=flat-square)]()

通过模拟真实键盘输入（SendInput），将剪贴板内容逐字"敲"入目标窗口，完美解决远程桌面 / VNC 中特殊字符丢失或乱码的问题。

[快速开始](#-快速开始) · [功能特点](#-功能特点) · [工作原理](#-工作原理) · [配置说明](#-配置说明)

</div>

---

## 📑 目录

- [功能特点](#-功能特点)
- [工作原理](#-工作原理)
- [快速开始](#-快速开始)
- [配置说明](#-配置说明)
- [文件结构](#-文件结构)
- [适用场景](#-适用场景)
- [系统要求](#-系统要求)
- [常见问题](#-常见问题)
- [贡献指南](#-贡献指南)
- [许可证](#-许可证)

---

## ✨ 功能特点

- ⚡ **快捷键触发** — `Ctrl+Alt+V` 一键触发模拟键盘输入粘贴
- 🔣 **特殊字符支持** — 正确处理 `"` `'` `>` `<` `*` `;` `&` `|` 等特殊字符
- 🐢 **速度可调** — 字符间延迟 1–200ms 可调节，适配不同窗口响应速度
- ⏱️ **首字延迟** — 输入前等待 0–2000ms，确保窗口焦点就绪后再开始输入
- 📥 **后台运行** — 系统托盘常驻，不干扰其他操作
- 🔒 **防重复** — 互斥锁防止多实例运行

---

## 🔧 工作原理

```
剪贴板文本
    │
    ▼
┌─────────────┐
│  字符分类器  │
└──────┬──────┘
       │
   ┌───┴───┐
   ▼       ▼
普通字符  特殊字符
   │       │
   ▼       ▼
Unicode   ScanCode
模式      模式
   │       │
   └───┬───┘
       ▼
  SendInput API
       │
       ▼
  目标窗口（远程桌面/VNC）
```

- **普通字符**：使用 Unicode 模式（`KEYEVENTF_UNICODE`），效率高
- **特殊字符**：使用扫描码模式（ScanCode），确保远程桌面协议正确接收

---

## 🚀 快速开始

### 方式一：运行已编译程序

1. 下载 `dist/键盘粘贴工具.exe`
2. 双击运行，程序自动启动并最小化到系统托盘
3. 用 `Ctrl+C` 复制需要粘贴的文本
4. 切换到目标窗口，按 `Ctrl+Alt+V` 触发模拟输入

### 方式二：从源码运行

```bash
# 克隆仓库
git clone https://github.com/StaLincon/keyboard-paste-tool.git
cd keyboard-paste-tool

# 安装依赖
pip install -r requirements.txt

# 运行
python main.py
```

### 方式三：打包为 exe

```bash
# 使用一键打包脚本
build.bat

# 或手动打包
pyinstaller --onefile --noconsole --name "键盘粘贴工具" ^
  --add-data "keyboard_handler.py;." ^
  --add-data "ui.py;." ^
  --hidden-import keyboard ^
  --hidden-import pyperclip ^
  --hidden-import pystray ^
  --hidden-import PIL ^
  --hidden-import PIL.Image ^
  --hidden-import PIL.ImageDraw ^
  --hidden-import tkinter ^
  --hidden-import ctypes ^
  --hidden-import ctypes.wintypes main.py
```

---

## ⚙️ 配置说明

右键系统托盘图标 → **设置**，可调整以下参数：

| 设置项 | 默认值 | 范围 | 说明 |
|--------|--------|------|------|
| 字符间延迟 | 5ms | 1–200ms | 控制输入速度，远程桌面建议 10–50ms |
| 首字前延迟 | 200ms | 0–2000ms | 防止切换窗口时开头字符丢失 |

---

## 📂 文件结构

```
├── main.py              # 主入口，集成系统托盘与热键监听
├── keyboard_handler.py  # 核心模块：SendInput 键盘模拟 + 字符分类
├── ui.py                # 设置面板（tkinter）
├── requirements.txt     # Python 依赖列表
├── build.bat            # 一键打包脚本（PyInstaller）
└── dist/                # 打包输出目录（exe 在此）
```

---

## 🎯 适用场景

- 🔴 远程桌面连接到 Kali Linux（RDP 特殊字符乱码）
- 🟡 VNC 连接到远程虚拟机
- 🟢 任何需要模拟真实键盘输入的场景（自动化测试、批量输入等）

---

## 💻 系统要求

| 项目 | 要求 |
|------|------|
| 操作系统 | Windows 10 及以上 |
| Python（开发） | 3.8+ |
| 运行已编译 exe | 无需 Python 环境 |

---

## ❓ 常见问题

**Q: 按了快捷键没反应？**
A: 确认程序正在运行（系统托盘有图标），且目标窗口已获得焦点。部分全屏程序可能拦截热键。

**Q: 输入速度太快导致丢字？**
A: 在设置中增大"字符间延迟"，远程桌面建议 20–50ms。

**Q: 开头几个字符丢失？**
A: 增大"首字前延迟"，给窗口切换留出时间。

**Q: 中文无法输入？**
A: 当前版本主要面向代码/命令行等 ASCII 文本场景，中文输入依赖目标窗口的输入法状态。

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/xxx`)
3. 提交更改 (`git commit -m 'Add xxx'`)
4. 推送 (`git push origin feature/xxx`)
5. 开启 Pull Request

---

## 📄 许可证

本项目采用 MIT License 开源协议。
