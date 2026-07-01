"""
键盘粘贴工具 - 主入口

功能：
- Ctrl+Alt+V 触发模拟键盘输入粘贴
- 系统托盘后台运行
- 设置面板（输入速度调节）
- 解决远程 Kali 虚拟机中特殊字符转换问题
"""

import sys
import os
import threading
import ctypes

# 隐藏控制台窗口（仅当以 .pyw 或打包后的 .exe 运行时）
if sys.executable.endswith("pythonw.exe") or getattr(sys, 'frozen', False):
    try:
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    except Exception:
        pass

from keyboard_handler import KeyboardHandler
from ui import SettingsWindow


def create_tray_icon(ui: SettingsWindow, handler: KeyboardHandler):
    """
    创建系统托盘图标。
    使用 pystray + PIL 生成简单图标。
    """
    try:
        from PIL import Image, ImageDraw
        import pystray
    except ImportError:
        print("[警告] pystray 或 Pillow 未安装，系统托盘功能不可用")
        return None

    # 生成一个简单的图标（绿色圆形 = 运行中）
    def create_image(color):
        size = 64
        image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        margin = 4
        draw.ellipse(
            [margin, margin, size - margin, size - margin],
            fill=color,
            outline=(255, 255, 255),
            width=2
        )
        # 画一个 K 字母
        draw.text(
            (size // 2 - 2, size // 2 - 2),
            "K",
            fill=(255, 255, 255),
            anchor="mm"
        )
        return image

    icon = pystray.Icon(
        "keyboard_paste_tool",
        create_image((0, 180, 0)),
        "键盘粘贴工具 (自定义热键)",
        menu=pystray.Menu(
            pystray.MenuItem("显示设置", lambda: ui.restore()),
            pystray.MenuItem("切换服务", lambda: toggle_service(handler)),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("退出", lambda: exit_app(handler, icon, ui)),
        )
    )

    # 更新图标颜色
    def update_icon_color(is_running):
        if is_running:
            icon.icon = create_image((0, 180, 0))  # 绿色
        else:
            icon.icon = create_image((180, 0, 0))  # 红色

    handler.set_on_status_change(update_icon_color)

    return icon


def toggle_service(handler: KeyboardHandler):
    """切换服务状态"""
    if handler.is_running:
        handler.stop()
    else:
        try:
            handler.start()
        except Exception as e:
            print(f"[错误] 切换服务失败: {e}")


def exit_app(handler: KeyboardHandler, icon, ui: SettingsWindow):
    """退出应用"""
    if handler.is_running:
        handler.stop()
    if icon:
        icon.stop()
    ui.destroy()
    os._exit(0)


def main():
    """主函数"""
    # 防止重复运行
    try:
        import ctypes.wintypes
        mutex_name = "Global\\KeyboardPasteTool_Mutex"
        mutex = ctypes.windll.kernel32.CreateMutexW(None, False, mutex_name)
        if ctypes.windll.kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
            print("[提示] 程序已在运行中，请检查系统托盘")
            # 尝试激活已有窗口
            try:
                ctypes.windll.user32.FindWindowW(None, "键盘粘贴工具 - 设置")
            except Exception:
                pass
            return
    except Exception:
        pass

    # 创建键盘处理器
    handler = KeyboardHandler(delay_ms=5)

    # 创建 UI
    ui = SettingsWindow(handler)

    # 创建系统托盘图标
    icon = create_tray_icon(ui, handler)

    # 启动托盘图标（在后台线程运行）
    if icon:
        tray_thread = threading.Thread(target=icon.run, daemon=True)
        tray_thread.start()

    # 自动启动服务
    try:
        handler.start()
    except Exception as e:
        print(f"[警告] 自动启动服务失败: {e}")

    # 显示 UI 主窗口
    try:
        ui.show()
    except KeyboardInterrupt:
        pass
    finally:
        if handler.is_running:
            handler.stop()
        if icon:
            icon.stop()


if __name__ == "__main__":
    main()