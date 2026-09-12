@echo off
chcp 65001 >nul
rem ============================================================
rem  热键模式.bat —— 常驻后台，按 Ctrl+Alt+Q 随时关屏
rem  用一个黑窗口保持运行，不需要了直接关掉这个窗口即可
rem ============================================================

set "PY=C:\Users\15274\.workbuddy\binaries\python\envs\default\Scripts\python.exe"
if not exist "%PY%" set "PY=python"

title 关屏热键（Ctrl+Alt+Q）——关闭本窗口即退出
"%PY%" "%~dp0screen_off.py" --hotkey
pause
