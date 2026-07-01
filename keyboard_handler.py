"""
键盘处理模块 - 全局热键监听 + 键盘输入模拟

使用 SendInput API 底层模拟真实键盘输入，解决远程 Kali 虚拟机中的
特殊字符转换问题（", >, <, *, ; 等）。
"""

import ctypes
import ctypes.wintypes as wintypes
import threading
import time
import pyperclip
import keyboard

# ============================================================
# Windows API 定义
# ============================================================
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# 输入类型常量
INPUT_KEYBOARD = 1
KEYEVENTF_KEYDOWN = 0x0000
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
KEYEVENTF_SCANCODE = 0x0008

# 虚拟键码
VK_SHIFT = 0x10
VK_CONTROL = 0x11
VK_MENU = 0x12  # Alt

# GetKeyboardLayout
GetKeyboardLayout = user32.GetKeyboardLayout
GetKeyboardLayout.restype = wintypes.HANDLE
GetKeyboardLayout.argtypes = [wintypes.DWORD]

# MapVirtualKeyEx
MapVirtualKeyEx = user32.MapVirtualKeyExW
MapVirtualKeyEx.restype = wintypes.UINT
MapVirtualKeyEx.argtypes = [wintypes.UINT, wintypes.UINT, wintypes.HANDLE]

MAPVK_VK_TO_VSC = 0
MAPVK_VSC_TO_VK = 1

# VkKeyScanEx
VkKeyScanEx = user32.VkKeyScanExW
VkKeyScanEx.restype = ctypes.c_short
VkKeyScanEx.argtypes = [wintypes.WCHAR, wintypes.HANDLE]

# SendInput
class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD),
    ]


class INPUT_UNION(ctypes.Union):
    _fields_ = [
        ("ki", KEYBDINPUT),
        ("mi", MOUSEINPUT),
        ("hi", HARDWAREINPUT),
    ]


class INPUT(ctypes.Structure):
    _fields_ = [
        ("type", wintypes.DWORD),
        ("union", INPUT_UNION),
    ]


SendInput = user32.SendInput
SendInput.restype = wintypes.UINT
SendInput.argtypes = [wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int]


# ============================================================
# 键盘模拟核心
# ============================================================

class KeyboardHandler:
    """键盘处理器：监听全局热键并通过 SendInput 模拟键盘输入"""

    def __init__(self, delay_ms: int = 5, pre_delay_ms: int = 200, hotkey: str = "ctrl+alt+v"):
        self._delay = max(1, min(delay_ms, 200))  # 字符间延迟 1-200ms
        self._pre_delay = max(0, min(pre_delay_ms, 2000))  # 首字前等待 0-2000ms
        self._hotkey = hotkey.lower()  # 当前热键字符串
        self._running = False
        self._hotkey_id = None
        self._lock = threading.Lock()
        self._typing = False  # 是否正在模拟输入中

        # 状态回调
        self._on_status_change = None
        self._on_typing_start = None
        self._on_typing_end = None

    # ----- 属性 -----
    @property
    def delay_ms(self) -> int:
        return self._delay

    @delay_ms.setter
    def delay_ms(self, value: int):
        self._delay = max(1, min(value, 200))

    @property
    def pre_delay_ms(self) -> int:
        return self._pre_delay

    @pre_delay_ms.setter
    def pre_delay_ms(self, value: int):
        self._pre_delay = max(0, min(value, 2000))

    @property
    def hotkey(self) -> str:
        return self._hotkey

    @hotkey.setter
    def hotkey(self, value: str):
        self._hotkey = value.lower().strip()

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def is_typing(self) -> bool:
        return self._typing

    # ----- 回调设置 -----
    def set_on_status_change(self, callback):
        self._on_status_change = callback

    def set_on_typing_start(self, callback):
        self._on_typing_start = callback

    def set_on_typing_end(self, callback):
        self._on_typing_end = callback

    # ----- 字符输入（使用 SendInput UNICODE） -----
    def _send_unicode_char(self, char: str):
        """
        使用 SendInput + KEYEVENTF_UNICODE 发送单个 Unicode 字符。
        此方法绕过键盘布局，直接发送字符，对远程 VM 最可靠。
        """
        if not char:
            return

        code_point = ord(char)

        inp_down = INPUT()
        inp_down.type = INPUT_KEYBOARD
        inp_down.union.ki.wVk = 0
        inp_down.union.ki.wScan = code_point
        inp_down.union.ki.dwFlags = KEYEVENTF_UNICODE
        inp_down.union.ki.time = 0
        inp_down.union.ki.dwExtraInfo = None

        inp_up = INPUT()
        inp_up.type = INPUT_KEYBOARD
        inp_up.union.ki.wVk = 0
        inp_up.union.ki.wScan = code_point
        inp_up.union.ki.dwFlags = KEYEVENTF_UNICODE | KEYEVENTF_KEYUP
        inp_up.union.ki.time = 0
        inp_up.union.ki.dwExtraInfo = None

        inputs = (INPUT * 2)(inp_down, inp_up)
        SendInput(2, inputs, ctypes.sizeof(INPUT))

    def _send_vk_char(self, char: str):
        """
        使用虚拟键码 + 扫描码模拟按键（备选方案）。
        通过 VkKeyScanEx 获取虚拟键码和 Shift 状态，再通过 MapVirtualKeyEx
        获取扫描码，最后用 SendInput 发送。
        """
        if not char:
            return

        layout = GetKeyboardLayout(0)
        vk_result = VkKeyScanEx(char, layout)
        if vk_result == -1:
            # 无法映射，使用 Unicode 方式
            self._send_unicode_char(char)
            return

        vk = vk_result & 0xFF
        shift_state = (vk_result >> 8) & 0xFF

        # 扫描码
        scan = MapVirtualKeyEx(vk, MAPVK_VK_TO_VSC, layout)

        # 需要按下的修饰键
        needs_shift = bool(shift_state & 1)
        needs_ctrl = bool(shift_state & 2)
        needs_alt = bool(shift_state & 4)

        # 输入序列
        inputs = []
        modifier_flags = []

        if needs_shift:
            modifier_flags.append(VK_SHIFT)
        if needs_ctrl:
            modifier_flags.append(VK_CONTROL)
        if needs_alt:
            modifier_flags.append(VK_MENU)

        # 按下修饰键
        for vk_mod in modifier_flags:
            inp = INPUT()
            inp.type = INPUT_KEYBOARD
            inp.union.ki.wVk = vk_mod
            inp.union.ki.wScan = MapVirtualKeyEx(vk_mod, MAPVK_VK_TO_VSC, layout)
            inp.union.ki.dwFlags = KEYEVENTF_SCANCODE
            inp.union.ki.time = 0
            inp.union.ki.dwExtraInfo = None
            inputs.append(inp)

        # 按下目标键
        inp_down = INPUT()
        inp_down.type = INPUT_KEYBOARD
        inp_down.union.ki.wVk = vk
        inp_down.union.ki.wScan = scan
        inp_down.union.ki.dwFlags = KEYEVENTF_SCANCODE
        inp_down.union.ki.time = 0
        inp_down.union.ki.dwExtraInfo = None
        inputs.append(inp_down)

        # 释放目标键
        inp_up = INPUT()
        inp_up.type = INPUT_KEYBOARD
        inp_up.union.ki.wVk = vk
        inp_up.union.ki.wScan = scan
        inp_up.union.ki.dwFlags = KEYEVENTF_SCANCODE | KEYEVENTF_KEYUP
        inp_up.union.ki.time = 0
        inp_up.union.ki.dwExtraInfo = None
        inputs.append(inp_up)

        # 释放修饰键（逆序）
        for vk_mod in reversed(modifier_flags):
            inp = INPUT()
            inp.type = INPUT_KEYBOARD
            inp.union.ki.wVk = vk_mod
            inp.union.ki.wScan = MapVirtualKeyEx(vk_mod, MAPVK_VK_TO_VSC, layout)
            inp.union.ki.dwFlags = KEYEVENTF_SCANCODE | KEYEVENTF_KEYUP
            inp.union.ki.time = 0
            inp.union.ki.dwExtraInfo = None
            inputs.append(inp)

        if inputs:
            in_array = (INPUT * len(inputs))(*inputs)
            SendInput(len(inputs), in_array, ctypes.sizeof(INPUT))

    def _type_char(self, char: str):
        """
        键入单个字符。
        策略：优先使用虚拟键码+扫描码方式（对远程桌面最可靠），
        失败时回退到 Unicode 方式。
        """
        # 特殊字符列表 - 已知在远程 VM 中可能出错的字符
        # 对这些字符使用双保险策略
        PROBLEMATIC_CHARS = {'"', "'", '>', '<', '*', ';', ':', '&', '|',
                             '\\', '/', '?', '!', '@', '#', '$', '%', '^',
                             '(', ')', '-', '_', '+', '=', '{', '}', '[',
                             ']', '~', '`', ',', '.'}

        # 对于换行符，使用 Enter 键
        if char == '\n':
            self._send_vk_char('\r')  # 使用回车键
            return
        if char == '\r':
            return  # 跳过单独的 \r
        if char == '\t':
            self._send_vk_char('\t')
            return

        # 对特殊字符使用虚拟键码+扫描码方式
        if char in PROBLEMATIC_CHARS:
            self._send_vk_char(char)
        else:
            # 普通字符使用 Unicode 方式（更简单可靠）
            self._send_unicode_char(char)

    def type_text(self, text: str):
        """
        模拟键盘逐字输入文本。

        Args:
            text: 要输入的文本内容
        """
        if not text:
            return

        with self._lock:
            self._typing = True
            if self._on_typing_start:
                self._on_typing_start()

            try:
                # 首字前等待，避免切换窗口时开头字符丢失
                if self._pre_delay > 0:
                    time.sleep(self._pre_delay / 1000.0)

                delay = self._delay / 1000.0  # 转换为秒
                for i, char in enumerate(text):
                    self._type_char(char)
                    time.sleep(delay)
            except Exception as e:
                print(f"[错误] 输入过程中发生异常: {e}")
            finally:
                self._typing = False
                if self._on_typing_end:
                    self._on_typing_end()

    # ----- 剪贴板读取 -----
    def _get_clipboard_text(self) -> str:
        """读取剪贴板文本内容"""
        try:
            text = pyperclip.paste()
            return text if text else ""
        except Exception as e:
            print(f"[错误] 读取剪贴板失败: {e}")
            return ""

    # ----- 热键回调 -----
    def _on_hotkey(self):
        """热键触发时的回调"""
        if self._typing:
            print("[提示] 正在输入中，请等待当前输入完成")
            return

        text = self._get_clipboard_text()
        if not text:
            print("[提示] 剪贴板为空")
            return

        print(f"[信息] 开始输入 {len(text)} 个字符，延迟 {self._delay}ms")
        threading.Thread(target=self.type_text, args=(text,), daemon=True).start()

    # ----- 启动/停止 / 热键切换 -----
    def start(self):
        """注册全局热键并开始监听"""
        if self._running:
            return

        try:
            self._hotkey_id = keyboard.add_hotkey(
                self._hotkey,
                self._on_hotkey,
                suppress=False,
                trigger_on_release=False
            )
            self._running = True
            print(f"[信息] 键盘处理器已启动，快捷键: {self._hotkey}")
            if self._on_status_change:
                self._on_status_change(True)
        except Exception as e:
            print(f"[错误] 启动键盘处理器失败: {e}")
            raise

    def stop(self):
        """注销热键并停止监听"""
        if not self._running:
            return

        try:
            if self._hotkey_id is not None:
                keyboard.remove_hotkey(self._hotkey_id)
                self._hotkey_id = None
            self._running = False
            print("[信息] 键盘处理器已停止")
            if self._on_status_change:
                self._on_status_change(False)
        except Exception as e:
            print(f"[错误] 停止键盘处理器失败: {e}")
            self._running = False

    def set_hotkey(self, new_hotkey: str) -> bool:
        """
        运行时切换热键。需要先停止再重新启动。

        Args:
            new_hotkey: 新热键字符串，如 "ctrl+alt+v", "ctrl+shift+z" 等

        Returns:
            bool: 是否切换成功
        """
        new_hotkey = new_hotkey.lower().strip()
        if not new_hotkey:
            print("[错误] 热键不能为空")
            return False

        was_running = self._running
        if was_running:
            self.stop()

        self._hotkey = new_hotkey

        if was_running:
            try:
                self.start()
                print(f"[信息] 热键已切换为: {self._hotkey}")
                return True
            except Exception as e:
                print(f"[错误] 切换热键失败: {e}")
                return False
        return True