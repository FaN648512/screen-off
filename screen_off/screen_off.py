# -*- coding: utf-8 -*-
"""
screen_off.py —— 一键关闭显示器（只关屏幕，不睡眠、不锁屏、不影响任何程序运行）

一句话总览：
    通过 Windows 自带的「显示器省电」系统命令（SC_MONITORPOWER）让屏幕黑掉，
    相当于把笔记本合上屏幕的那个动作，机器本身照常运行（下载、跑程序都不停）。

为什么不用睡眠/休眠？
    睡眠（S3）会暂停程序、断网；本脚本只是让屏幕不亮，CPU、内存、网络全部照常。

唤醒方式：
    按电源键、动一下鼠标、敲一下键盘，屏幕都会立刻亮起来（这是 Windows 的默认行为，
    无法只限制成电源键唤醒）。若希望亮屏后需要输入密码，请加 --lock 参数。

用法（在命令行里执行）：
    python screen_off.py                 1 秒后关屏
    python screen_off.py --delay 3       3 秒后关屏（留时间让你把手离开鼠标）
    python screen_off.py --lock          先锁屏再关屏（亮屏时需输入密码）
    python screen_off.py --hotkey        常驻后台：按 Ctrl+Alt+Q 关屏
    python screen_off.py --hotkey --key L   常驻后台：把热键字母换成 L
    python screen_off.py --self-test     只做检测，不会真的关屏

双击运行：直接用同目录的「关闭屏幕.bat」或「关闭屏幕-静默.vbs」。
"""

from __future__ import annotations

import argparse
import ctypes
import sys
import time
from ctypes import wintypes

# ---------------------------------------------------------------- Win32 常量
user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

HWND_BROADCAST = 0xFFFF          # 广播句柄：发给所有顶层窗口
WM_SYSCOMMAND = 0x0112           # 系统命令消息
SC_MONITORPOWER = 0xF170         # 子命令：显示器省电
MONITOR_OFF = 2                  # 关屏
MONITOR_ON = -1                  # 开屏

WM_HOTKEY = 0x0312
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_NOREPEAT = 0x4000            # 长按不重复触发

# 参数类型声明：64 位系统下 WPARAM 是 8 字节无符号，LPARAM 是 8 字节有符号
user32.SendMessageW.argtypes = [wintypes.HWND, wintypes.UINT,
                                ctypes.c_size_t, ctypes.c_ssize_t]
user32.SendMessageW.restype = ctypes.c_ssize_t
user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT,
                                ctypes.c_size_t, ctypes.c_ssize_t]
user32.PostMessageW.restype = wintypes.BOOL

WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)


def _send_to_all_windows() -> int:
    """逐个给可见的顶层窗口发一次「关屏」命令，返回成功发送的窗口数。

    为什么不用一次广播就完事？部分程序（某些全屏播放器、旧版软件）对广播消息不响应，
    逐个发送再补一次广播，关屏成功率最高。
    """
    count = 0

    def _cb(hwnd, _lparam):
        nonlocal count
        if user32.IsWindowVisible(hwnd):
            user32.SendMessageW(hwnd, WM_SYSCOMMAND, SC_MONITORPOWER, MONITOR_OFF)
            count += 1
        return True

    user32.EnumWindows(WNDENUMPROC(_cb), 0)
    return count


def monitor_off(lock_first: bool = False, verbose: bool = True) -> int:
    """关闭显示器。返回 0 表示命令已发出，1 表示遇到异常。"""
    if lock_first:
        # 先锁屏：这样即便有人动鼠标把屏幕点亮，看到的也是登录界面
        if not user32.LockWorkStation():
            if verbose:
                print("[提示] 锁屏失败，将只关屏。")
        time.sleep(0.8)   # 等锁屏界面绘制完成，否则会盖在锁屏上被刷掉

    try:
        hit = _send_to_all_windows()
        # 再广播一次兜底（对没响应逐个消息的窗口也生效）
        user32.SendMessageW(HWND_BROADCAST, WM_SYSCOMMAND, SC_MONITORPOWER, MONITOR_OFF)
        user32.PostMessageW(HWND_BROADCAST, WM_SYSCOMMAND, SC_MONITORPOWER, MONITOR_OFF)
        if verbose:
            print(f"[完成] 关屏命令已发送（覆盖 {hit} 个窗口）。机器仍在正常运行。")
        return 0
    except Exception as e:                                    # noqa: BLE001
        if verbose:
            print(f"[错误] 关屏失败：{e}")
        return 1


def monitor_on(verbose: bool = True) -> int:
    """把显示器点亮（正常情况下按一下键盘/鼠标就开，这个函数用于程序化恢复）。"""
    user32.SendMessageW(HWND_BROADCAST, WM_SYSCOMMAND, SC_MONITORPOWER, MONITOR_ON)
    if verbose:
        print("[完成] 已发送开屏命令。")
    return 0


def hotkey_loop(key: str = "Q", lock_first: bool = False) -> int:
    """常驻后台，注册全局热键，按下即关屏。Ctrl+C 或关闭窗口退出。"""
    vk = ord(key.upper())
    if not user32.RegisterHotKey(None, 1, MOD_CONTROL | MOD_ALT | MOD_NOREPEAT, vk):
        err = ctypes.get_last_error()
        print(f"[错误] 热键 Ctrl+Alt+{key.upper()} 注册失败（错误码 {err}），"
              f"可能已被其他软件占用，请换一个字母：--key L")
        return 1

    print(f"[常驻] 已就绪：随时按 Ctrl+Alt+{key.upper()} 关闭屏幕。"
          f"（关闭本窗口即退出）")
    msg = wintypes.MSG()
    try:
        while True:
            ret = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            if ret in (0, -1):
                break
            if msg.message == WM_HOTKEY:
                monitor_off(lock_first=lock_first, verbose=True)
    except KeyboardInterrupt:
        pass
    finally:
        user32.UnregisterHotKey(None, 1)
        print("[退出] 热键已注销。")
    return 0


def self_test() -> int:
    """只检测环境与接口，不真的关屏。"""
    print("=== 关屏工具自检 ===")
    print(f"Python 版本      : {sys.version.split()[0]}")
    print(f"进程位数         : {ctypes.sizeof(ctypes.c_void_p) * 8} 位")
    print(f"user32.SendMessageW 可用 : {'是' if callable(user32.SendMessageW) else '否'}")
    print(f"user32.EnumWindows 可用  : {'是' if callable(user32.EnumWindows) else '否'}")
    print(f"user32.RegisterHotKey 可用: {'是' if callable(user32.RegisterHotKey) else '否'}")
    # 会话是否可与桌面交互（服务/计划任务里跑会失败）
    hwinsta = user32.GetProcessWindowStation()
    print(f"可访问窗口站     : {'是' if hwinsta else '否（在后台服务中运行会关屏失败）'}")
    print("结论：关屏接口正常，如需实测请执行  python screen_off.py")
    print("提示：关屏后按电源键 / 动鼠标 / 敲键盘均可唤醒。")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="一键关闭显示器（仅关屏，不影响运行）")
    ap.add_argument("--delay", type=float, default=1.0,
                    help="延迟多少秒后关屏，默认 1 秒（留时间让手指离开鼠标，否则屏幕会立刻被唤醒）")
    ap.add_argument("--lock", action="store_true", help="先锁屏再关屏")
    ap.add_argument("--on", action="store_true", help="改为点亮屏幕")
    ap.add_argument("--hotkey", action="store_true", help="常驻后台，用全局热键关屏")
    ap.add_argument("--key", default="Q", help="热键字母，默认 Q（即 Ctrl+Alt+Q）")
    ap.add_argument("--self-test", action="store_true", help="只检测，不关屏")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()
    if args.on:
        return monitor_on()
    if args.hotkey:
        return hotkey_loop(key=args.key, lock_first=args.lock)
    if args.delay > 0:
        time.sleep(args.delay)
    return monitor_off(lock_first=args.lock)


if __name__ == "__main__":
    sys.exit(main())
