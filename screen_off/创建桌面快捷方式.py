# -*- coding: utf-8 -*-
"""创建桌面快捷方式.py —— 在桌面生成「关闭屏幕」快捷方式（带图标 + 全局热键 Ctrl+Alt+Q）

直接双击运行即可（同目录下的「创建桌面快捷方式.vbs」是同功能的无依赖版本）。
重复运行是安全的：会覆盖更新已有的快捷方式（换了图标后可用它刷新）。
"""
from __future__ import annotations

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
EXE = os.path.join(BASE, "关闭屏幕.exe")
# 图标：优先用 light 主题的独立 ico（命名独立 → 不受 Windows 图标缓存影响），
# 其次退回通用的 关闭屏幕.ico，最后退回 exe 自带图标
ICO_CANDIDATES = ["图标-light.ico", "关闭屏幕.ico"]


def main() -> int:
    if not os.path.exists(EXE):
        print(f"[错误] 没找到 {EXE}")
        return 1
    try:
        from win32com.client import Dispatch
    except ImportError:
        print("[错误] 缺少 pywin32，可执行："
              "pip install pywin32 -i https://pypi.tuna.tsinghua.edu.cn/simple")
        return 1

    shell = Dispatch("WScript.Shell")
    desktop = shell.SpecialFolders("Desktop")
    lnk_path = os.path.join(desktop, "关闭屏幕.lnk")

    lnk = shell.CreateShortcut(lnk_path)
    lnk.TargetPath = EXE
    lnk.Arguments = "--delay 1"
    lnk.WorkingDirectory = BASE
    lnk.Hotkey = "CTRL+ALT+Q"
    lnk.Description = "只关显示器，不影响运行（全局热键 Ctrl+Alt+Q）"
    for name in ICO_CANDIDATES:
        p = os.path.join(BASE, name)
        if os.path.exists(p):
            lnk.IconLocation = p + ",0"
            break
    else:
        lnk.IconLocation = EXE + ",0"
    lnk.Save()

    print(f"[完成] 已创建桌面快捷方式：{lnk_path}")
    print(f"       图标：{lnk.IconLocation}")
    print("       全局热键：Ctrl+Alt+Q（按下即关屏）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
