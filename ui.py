"""
UI 界面模块 - 设置面板

使用 tkinter 构建，提供：
- 输入速度调节滑块（1-200ms）
- 服务状态显示（运行中/已停止/输入中）
- 启动/停止按钮
- 最小化到系统托盘
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os


class SettingsWindow:
    """设置窗口"""

    def __init__(self, handler, on_close_callback=None):
        """
        Args:
            handler: KeyboardHandler 实例
            on_close_callback: 窗口关闭时的回调
        """
        self._handler = handler
        self._on_close_callback = on_close_callback
        self._window = None
        self._minimized_to_tray = False

        # 状态变量
        self._status_text = None
        self._delay_var = None
        self._delay_label = None
        self._start_stop_btn = None

        self._build_window()

    def _build_window(self):
        """构建窗口界面"""
        self._window = tk.Tk()
        self._window.title("键盘粘贴工具 - 设置")
        self._window.geometry("420x460")
        self._window.resizable(False, False)

        # 窗口图标（如果有的话）
        icon_path = os.path.join(os.path.dirname(__file__), "icon.ico")
        if os.path.exists(icon_path):
            self._window.iconbitmap(icon_path)

        # 窗口居中
        self._window.update_idletasks()
        w = self._window.winfo_width()
        h = self._window.winfo_height()
        x = (self._window.winfo_screenwidth() // 2) - (w // 2)
        y = (self._window.winfo_screenheight() // 2) - (h // 2)
        self._window.geometry(f"+{x}+{y}")

        # 关闭窗口时的行为
        self._window.protocol("WM_DELETE_WINDOW", self._on_close)

        # 样式
        style = ttk.Style()
        style.theme_use("clam")

        # 主框架
        main_frame = ttk.Frame(self._window, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # ----- 标题 -----
        title_label = ttk.Label(
            main_frame,
            text="键盘粘贴工具",
            font=("Microsoft YaHei UI", 16, "bold")
        )
        title_label.pack(pady=(0, 5))

        subtitle_label = ttk.Label(
            main_frame,
            text="Ctrl+Alt+V 模拟键盘输入粘贴",
            font=("Microsoft YaHei UI", 9),
            foreground="#666"
        )
        subtitle_label.pack(pady=(0, 15))

        # ----- 分隔线 -----
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)

        # ----- 状态区域 -----
        status_frame = ttk.LabelFrame(main_frame, text="服务状态", padding=10)
        status_frame.pack(fill=tk.X, pady=(10, 5))

        status_inner = ttk.Frame(status_frame)
        status_inner.pack(fill=tk.X)

        self._status_text = tk.StringVar(value="已停止")

        # 状态指示灯
        self._status_canvas = tk.Canvas(status_inner, width=16, height=16, highlightthickness=0)
        self._status_canvas.pack(side=tk.LEFT, padx=(0, 8))
        self._status_indicator = self._status_canvas.create_oval(
            2, 2, 14, 14, fill="red", outline=""
        )

        status_label = ttk.Label(
            status_inner,
            textvariable=self._status_text,
            font=("Microsoft YaHei UI", 11, "bold")
        )
        status_label.pack(side=tk.LEFT)

        # 快捷键提示
        shortcut_label = ttk.Label(
            status_inner,
            text="  (Ctrl+Alt+V)",
            font=("Microsoft YaHei UI", 9),
            foreground="#888"
        )
        shortcut_label.pack(side=tk.LEFT)

        # ----- 首字延迟设置 -----
        pre_delay_frame = ttk.LabelFrame(main_frame, text="首字前延迟（防止开头字符丢失）", padding=10)
        pre_delay_frame.pack(fill=tk.X, pady=(10, 5))

        self._pre_delay_var = tk.IntVar(value=self._handler.pre_delay_ms)

        pre_delay_inner = ttk.Frame(pre_delay_frame)
        pre_delay_inner.pack(fill=tk.X)

        ttk.Label(pre_delay_inner, text="输入前等待:").pack(side=tk.LEFT)

        self._pre_delay_label = ttk.Label(
            pre_delay_inner,
            text=f"{self._pre_delay_var.get()} ms",
            width=8,
            anchor=tk.E,
            font=("Microsoft YaHei UI", 10, "bold")
        )
        self._pre_delay_label.pack(side=tk.RIGHT)

        pre_delay_slider = ttk.Scale(
            pre_delay_frame,
            from_=0, to=2000,
            variable=self._pre_delay_var,
            orient=tk.HORIZONTAL,
            command=self._on_pre_delay_change,
            length=350
        )
        pre_delay_slider.pack(fill=tk.X, pady=(5, 0))

        pre_delay_hint = ttk.Label(
            pre_delay_frame,
            text="0ms = 无延迟  |  200ms = 默认  |  2000ms = 最大等待（切换窗口后确保焦点就绪）",
            font=("Microsoft YaHei UI", 8),
            foreground="#999"
        )
        pre_delay_hint.pack(pady=(5, 0))

        # ----- 速度设置 -----
        speed_frame = ttk.LabelFrame(main_frame, text="字符间延迟", padding=10)
        speed_frame.pack(fill=tk.X, pady=(10, 5))

        self._delay_var = tk.IntVar(value=self._handler.delay_ms)

        speed_inner = ttk.Frame(speed_frame)
        speed_inner.pack(fill=tk.X)

        ttk.Label(speed_inner, text="字符间延迟:").pack(side=tk.LEFT)

        self._delay_label = ttk.Label(
            speed_inner,
            text=f"{self._delay_var.get()} ms",
            width=8,
            anchor=tk.E,
            font=("Microsoft YaHei UI", 10, "bold")
        )
        self._delay_label.pack(side=tk.RIGHT)

        delay_slider = ttk.Scale(
            speed_frame,
            from_=1, to=200,
            variable=self._delay_var,
            orient=tk.HORIZONTAL,
            command=self._on_delay_change,
            length=350
        )
        delay_slider.pack(fill=tk.X, pady=(5, 0))

        # 速度说明
        speed_hint = ttk.Label(
            speed_frame,
            text="1ms = 极快（可能丢失字符）  |  50ms = 适中  |  200ms = 极慢（最稳定）",
            font=("Microsoft YaHei UI", 8),
            foreground="#999"
        )
        speed_hint.pack(pady=(5, 0))

        # ----- 按钮区域 -----
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(15, 0))

        self._start_stop_btn = ttk.Button(
            btn_frame,
            text="启动服务",
            command=self._toggle_service,
            width=15
        )
        self._start_stop_btn.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(
            btn_frame,
            text="测试输入",
            command=self._test_input,
            width=12
        ).pack(side=tk.LEFT)

        ttk.Button(
            btn_frame,
            text="最小化到托盘",
            command=self._minimize_to_tray,
            width=15
        ).pack(side=tk.RIGHT)

        # ----- 底部信息 -----
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))

        ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5, side=tk.BOTTOM)

        version_label = ttk.Label(
            bottom_frame,
            text="v1.0 | 适用: Windows 10+",
            font=("Microsoft YaHei UI", 8),
            foreground="#aaa"
        )
        version_label.pack(side=tk.LEFT)

        # 注册回调
        self._handler.set_on_status_change(self._update_status)
        self._handler.set_on_typing_start(self._on_typing_start)
        self._handler.set_on_typing_end(self._on_typing_end)

        # 初始状态
        if self._handler.is_running:
            self._update_status(True)

    # ----- 事件处理 -----
    def _on_delay_change(self, value):
        """延迟滑块变化"""
        delay = int(float(value))
        self._handler.delay_ms = delay
        self._delay_label.config(text=f"{delay} ms")

    def _on_pre_delay_change(self, value):
        """首字延迟滑块变化"""
        pre_delay = int(float(value))
        self._handler.pre_delay_ms = pre_delay
        self._pre_delay_label.config(text=f"{pre_delay} ms")

    def _toggle_service(self):
        """切换服务状态"""
        if self._handler.is_running:
            self._handler.stop()
        else:
            try:
                self._handler.start()
            except Exception as e:
                messagebox.showerror("错误", f"启动服务失败:\n{e}")

    def _update_status(self, is_running: bool):
        """更新状态显示（从非 UI 线程调用，使用 after 安全调度）"""
        def _update():
            if is_running:
                self._status_text.set("运行中")
                self._start_stop_btn.config(text="停止服务")
                self._status_canvas.itemconfig(self._status_indicator, fill="green")
            else:
                self._status_text.set("已停止")
                self._start_stop_btn.config(text="启动服务")
                self._status_canvas.itemconfig(self._status_indicator, fill="red")

        self._window.after(0, _update)

    def _on_typing_start(self):
        """开始输入时更新状态"""
        def _update():
            self._status_text.set("正在输入...")
            self._status_canvas.itemconfig(self._status_indicator, fill="orange")
        self._window.after(0, _update)

    def _on_typing_end(self):
        """结束输入时恢复状态"""
        def _update():
            if self._handler.is_running:
                self._status_text.set("运行中")
                self._status_canvas.itemconfig(self._status_indicator, fill="green")
            else:
                self._status_text.set("已停止")
                self._status_canvas.itemconfig(self._status_indicator, fill="red")
        self._window.after(0, _update)

    def _test_input(self):
        """测试输入功能"""
        import pyperclip
        test_text = pyperclip.paste()
        if not test_text or len(test_text.strip()) == 0:
            # 使用预定义测试文本
            test_text = (
                'echo "Hello Kali Linux" > test.txt\n'
                'echo "Special chars: ; * > < & |" \n'
                'ls -la /tmp/*.txt\n'
            )
            pyperclip.copy(test_text)
            messagebox.showinfo(
                "测试输入",
                "已复制测试文本到剪贴板。\n\n"
                "请按 Ctrl+Alt+V 在目标窗口中进行测试输入。\n\n"
                "测试内容包括:\n"
                '  - 双引号: "Hello Kali Linux"\n'
                "  - 分号: ;\n"
                "  - 星号: *\n"
                "  - 大于号: >\n"
                "  - 小于号: <\n"
                "  - 管道符: |\n"
                "  - 与号: &\n"
            )
        else:
            messagebox.showinfo(
                "测试输入",
                f"剪贴板内容 ({len(test_text)} 字符):\n\n"
                f"{test_text[:200]}{'...' if len(test_text) > 200 else ''}\n\n"
                "请按 Ctrl+Alt+V 在目标窗口中进行测试输入。"
            )

    def _minimize_to_tray(self):
        """最小化到系统托盘"""
        self._minimized_to_tray = True
        self._window.withdraw()

    def _on_close(self):
        """关闭窗口"""
        if self._handler.is_running:
            result = messagebox.askyesno(
                "确认退出",
                "服务正在运行中，确定要退出吗？\n\n"
                "选择「是」: 停止服务并退出\n"
                "选择「否」: 最小化到系统托盘"
            )
            if result:
                self._handler.stop()
                self._window.destroy()
                if self._on_close_callback:
                    self._on_close_callback()
            else:
                self._minimize_to_tray()
        else:
            self._window.destroy()
            if self._on_close_callback:
                self._on_close_callback()

    # ----- 公共方法 -----
    def show(self):
        """显示窗口"""
        if self._minimized_to_tray:
            self._window.deiconify()
            self._minimized_to_tray = False
        self._window.mainloop()

    def restore(self):
        """从托盘恢复窗口"""
        if self._minimized_to_tray:
            self._window.deiconify()
            self._minimized_to_tray = False

    def destroy(self):
        """销毁窗口"""
        try:
            self._window.destroy()
        except Exception:
            pass