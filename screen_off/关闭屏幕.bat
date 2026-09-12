@echo off
chcp 65001 >nul
rem ============================================================
rem  关闭屏幕.bat —— 双击即用：只关显示器，不睡眠、不影响运行
rem  便携写法：只认同目录下的 关闭屏幕.exe（自带 Python，零依赖）；
rem           没有 exe 时才用系统 PATH 里的 pythonw 跑同目录源码。
rem           任何一台 Windows 电脑拷过去都能直接用，无需安装。
rem  唤醒：按电源键 / 动鼠标 / 敲键盘
rem ============================================================

if exist "%~dp0关闭屏幕.exe" (
    start "" "%~dp0关闭屏幕.exe"
    goto :eof
)

where pythonw >nul 2>nul
if errorlevel 1 (
    echo 没找到 关闭屏幕.exe，系统里也没有 Python。
    echo 请把本文件和 关闭屏幕.exe 放在同一个文件夹里再双击。
    pause
    goto :eof
)

start "" pythonw "%~dp0screen_off.py" --delay 2
