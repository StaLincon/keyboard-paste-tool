@echo off
chcp 65001 >nul
echo ========================================
echo   键盘粘贴工具 - 打包脚本
echo ========================================
echo.

REM 检查 Python 是否安装
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

echo [1/4] 安装依赖...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [错误] 依赖安装失败
    pause
    exit /b 1
)

echo.
echo [2/4] 清理旧的构建文件...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

echo.
echo [3/4] 开始打包为 .exe...
pyinstaller ^
    --onefile ^
    --noconsole ^
    --name "键盘粘贴工具" ^
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
    --hidden-import ctypes.wintypes ^
    main.py

if %errorlevel% neq 0 (
    echo [错误] 打包失败
    pause
    exit /b 1
)

echo.
echo [4/4] 打包完成!
echo.
echo 输出文件: dist\键盘粘贴工具.exe
echo.
echo 提示: 如果杀毒软件误报，请将程序添加到白名单。
echo.

REM 可选：创建快捷方式到桌面
set /p create_shortcut="是否创建桌面快捷方式? (y/n): "
if /i "%create_shortcut%"=="y" (
    powershell -Command ^
        "$ws = New-Object -ComObject WScript.Shell; ^
        $s = $ws.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\键盘粘贴工具.lnk'); ^
        $s.TargetPath = '%cd%\dist\键盘粘贴工具.exe'; ^
        $s.WorkingDirectory = '%cd%\dist'; ^
        $s.Save()"
    echo 桌面快捷方式已创建。
)

echo.
echo 按任意键退出...
pause >nul