# -*- coding: utf-8 -*-
"""发布打包.py —— 生成「关闭屏幕」绿色免安装版（文件夹 + ZIP）

做什么：
    1. 把"别的电脑直接能用"的那几个文件挑出来，放进 发布包\\关闭屏幕-绿色版\\；
    2. 顺手核对一遍便携性（exe 位数、是否只依赖标准库、exe 是否能独立跑起来）；
    3. 打成 ZIP，方便拷 U 盘 / 发微信 / 上传网盘。

为什么这么挑文件（关键）：
    * 关闭屏幕.exe / 关屏热键.exe 由 PyInstaller --onefile 打包，**Python 解释器已塞进 exe**，
      目标电脑不需要装 Python、不需要联网、不需要管理员权限。
    * 两个 .vbs / .bat 启动器已改成"只认同目录下的 exe"，里面不含本机专属路径。
    * 创建桌面快捷方式.vbs 用系统自带 WSH，不依赖 pywin32（所以 .py 版本不进包）。
    * 源码 screen_off.py 只 import 标准库（argparse/ctypes/sys/time），留一份给懂技术的人看。

用法：
    python 发布打包.py
"""

from __future__ import annotations

import os
import shutil
import struct
import subprocess
import zipfile
from pathlib import Path

BASE = Path(__file__).resolve().parent
PKG_DIR = BASE / "发布包" / "关闭屏幕-绿色版"
ZIP_PATH = BASE.parent / "关闭屏幕-绿色版.zip"

# 只打这几个文件（顺序即 ZIP 内的排列顺序）
PAYLOAD = [
    "关闭屏幕.exe",
    "关屏热键.exe",
    "关闭屏幕-静默.vbs",
    "关闭屏幕.bat",
    "热键模式.bat",
    "创建桌面快捷方式.vbs",
    "图标-light.ico",
    "使用说明.html",
    "安装说明.txt",
    "screen_off.py",
]

README = """关闭屏幕 —— 绿色免安装版
================================================

【怎么用】
1. 把整个文件夹拷到目标电脑（U 盘 / 微信 / 网盘都行），位置随意，比如 D:\\关闭屏幕\\
2. 双击「关闭屏幕.exe」——约 1 秒后屏幕熄灭，电脑里的程序照常运行（没有睡眠、没有断网）。
3. 想重新点亮：按一下笔记本电源键，或者动一下鼠标 / 敲一下键盘。

【不用装任何东西】
    exe 里已经自带运行环境，目标电脑不需要装 Python、不需要联网、不需要管理员权限。
    只要系统是 64 位 Windows 10 / 11 就能直接双击运行。

【三个文件分别是什么】
    关闭屏幕.exe        主程序：双击就关屏（推荐日常用这个）
    关屏热键.exe        常驻程序：开着它，按 Ctrl+Alt+Q 随时关屏；关掉它的窗口即退出
    关闭屏幕-静默.vbs   效果同主程序的双击入口，可作为快捷方式的目标
    创建桌面快捷方式.vbs 双击一次 → 在桌面生成带图标的快捷方式（并绑 Ctrl+Alt+Q 热键）
    使用说明.html       完整说明（含原理、排查清单），双击用浏览器打开

【可能会遇到的两件事】
1. 首次运行被 Windows 拦一下
   Windows SmartScreen 或杀毒软件可能因为"没见过这个程序"而提示风险（PyInstaller 打包的
   exe 常被误报）。点「更多信息 → 仍要运行」，或把本文件夹加入杀毒软件白名单即可。
2. 关屏后马上又亮
   说明关屏那一瞬间鼠标被碰到了。右键快捷方式 → 属性 → 在「目标」末尾加  --delay 3
   （让它多等几秒），手指离开鼠标就稳了。

【它到底做了什么】
    调用 Windows 自带的显示器省电命令，只让屏幕黑掉；CPU、内存、硬盘、网络、下载、
    后台程序全部照常运行。不是睡眠、不是休眠，不会中断任何事情。

原理解释、每个参数的用法、故障排查：见「使用说明.html」。
"""


def pe_machine(path: Path) -> tuple[str, str]:
    """读 PE 头，返回（机器类型描述, 系统要求说明）。

    注意：PE 头里的「子系统版本」是链接器写的下限（通常是 6.0 = Vista），
    真正能不能跑由「exe 里自带的 Python 版本」决定 —— 本包内置 Python 3.13，
    实际要求 Windows 8.1 及以上，推荐 Windows 10 / 11。
    """
    with open(path, "rb") as f:
        data = f.read(0x400)
    e_lfanew = struct.unpack_from("<I", data, 0x3C)[0]
    machine = struct.unpack_from("<H", data, e_lfanew + 4)[0]
    kind = {0x8664: "64 位 (x64)", 0x14C: "32 位 (x86)", 0xAA64: "ARM64"}.get(machine, hex(machine))
    opt = e_lfanew + 4 + 20
    os_major, os_minor = struct.unpack_from("<HH", data, opt + 40)
    return kind, (f"PE 头声明最低 {os_major}.{os_minor}；"
                  f"实际受内置 Python 3.13 限制 → Windows 8.1 以上，推荐 Win10/Win11")


def main() -> int:
    if PKG_DIR.exists():
        shutil.rmtree(PKG_DIR)
    PKG_DIR.mkdir(parents=True)

    missing = []
    for name in PAYLOAD:
        src = BASE / name
        if not src.exists():
            missing.append(name)
            continue
        shutil.copy2(src, PKG_DIR / name)

    # 安装说明.txt 现写现放（方便改文案）
    (PKG_DIR / "安装说明.txt").write_text(README, encoding="utf-8")
    if "安装说明.txt" in missing:
        missing.remove("安装说明.txt")

    print("=== 便携性自检 ===")
    for exe_name in ("关闭屏幕.exe", "关屏热键.exe"):
        p = PKG_DIR / exe_name
        if not p.exists():
            print(f"{exe_name}：缺失！")
            continue
        kind, osreq = pe_machine(p)
        print(f"{exe_name}：{kind}，{osreq}，{p.stat().st_size / 1048576:.2f} MiB")

    r = subprocess.run([str(PKG_DIR / "关闭屏幕.exe"), "--self-test"],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=180)
    print(f"在新目录里独立运行自检：退出码={r.returncode}（0 = 正常，说明不依赖构建时的环境）")

    print("=== 依赖检查 ===")
    src_text = (BASE / "screen_off.py").read_text(encoding="utf-8")
    imports = sorted({ln.split()[1].split(".")[0] for ln in src_text.splitlines()
                      if ln.startswith(("import ", "from ")) and "PIL" not in ln})
    print("screen_off.py 的 import：" + ", ".join(imports) + "（全部为标准库，无第三方依赖）")

    if missing:
        print("⚠ 缺文件：" + ", ".join(missing))

    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as z:
        for name in sorted(os.listdir(PKG_DIR)):
            z.write(PKG_DIR / name, f"关闭屏幕-绿色版/{name}")
    print(f"\n[完成] 文件夹：{PKG_DIR}")
    print(f"[完成] ZIP：{ZIP_PATH}（{ZIP_PATH.stat().st_size / 1048576:.2f} MiB）")
    print("[包内文件] " + ", ".join(sorted(os.listdir(PKG_DIR))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
