# -*- coding: utf-8 -*-
"""制作图标.py —— 为「关闭屏幕」小工具生成简约图标（PNG 预览 + 多尺寸 ICO）

设计说明（图形含义，一眼能看懂）：
    * 白色圆角方块（纯白底，带一圈极浅的灰边，避免在白色桌面上"隐形"）；
    * 深蓝显示器轮廓 + 底座 = 这是一个"屏幕"相关的工具；
    * 屏幕里的浅蓝月牙 = 屏幕熄灭 / 息屏，正好对应本工具的功能（只关屏，不关机）。

两套配色（--theme 切换，默认 light）：
    light（当前使用）：纯白底 + 深蓝线条 + 浅蓝月牙
    dark （上一版）  ：深蓝渐变底 + 白色线条 + 青色月牙

实现要点：
    * 所有图形按目标尺寸成比例绘制，每个尺寸单独用 4 倍超采样后再缩小，
      这样 16×16 的小图标不会糊成一团（直接缩小 256 图标必然糊）。
    * 输出的 ICO 里打包 256/128/64/48/32/16 六个尺寸，Windows 会按场合自动挑。

用法：
    python 制作图标.py                     # 纯白版，生成到脚本所在目录
    python 制作图标.py --theme dark        # 生成旧的深蓝渐变版
    python 制作图标.py --out D:\\x         # 指定输出目录
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

SS = 4                       # 超采样倍数
SIZES = [256, 128, 64, 48, 32, 16]
SHEET_BG = (100, 116, 139)   # 尺寸对照图的底色（中性灰，白/深两版都看得清）

# ------------------------------------------------------------------ 配色
THEMES: dict[str, dict[str, tuple[int, int, int] | None]] = {
    # 纯白底（当前使用）：白底 + 深蓝线条 + 浅蓝月牙
    "light": {
        "bg_top": (255, 255, 255),
        "bg_bottom": (255, 255, 255),
        "outline_bg": (203, 213, 225),   # 外圈极浅灰边，防止白底在白桌面上隐形
        "panel": (255, 255, 255),        # 屏幕内部：同为纯白，靠深蓝描边界定
        "edge": (30, 64, 175),           # 显示器描边 / 底座：深蓝
        "moon": (56, 189, 248),          # 月牙：浅蓝
        "glow": (147, 197, 253),         # 底座下沿的一点环境光
    },
    # 深蓝渐变底（上一版）
    "dark": {
        "bg_top": (30, 64, 175),
        "bg_bottom": (11, 18, 32),
        "outline_bg": None,
        "panel": (22, 35, 61),
        "edge": (226, 232, 240),
        "moon": (125, 211, 252),
        "glow": (56, 189, 248),
    },
}


def _lerp(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))  # type: ignore[return-value]


def _gradient(size: int, top: tuple[int, int, int], bottom: tuple[int, int, int]) -> Image.Image:
    """竖直渐变底，用一条 1×size 的细条拉伸得到，效率高（纯色时上下同色即可）。"""
    strip = Image.new("RGB", (1, size))
    px = strip.load()
    for y in range(size):
        px[0, y] = _lerp(top, bottom, y / max(size - 1, 1))
    return strip.resize((size, size), Image.BILINEAR)


def _ell(box: tuple[int, int, int, int], size: int) -> Image.Image:
    """生成一个实心椭圆的 L 遮罩。"""
    m = Image.new("L", (size, size), 0)
    ImageDraw.Draw(m).ellipse(box, fill=255)
    return m


def render(size: int, theme: str = "light") -> Image.Image:
    """渲染单个尺寸的图标。size 是最终尺寸，内部按 SS 倍超采样绘制。"""
    c = THEMES[theme]
    s = size * SS
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))

    # 1) 圆角方块底（渐变或纯色）
    radius = int(0.22 * s)
    mask = Image.new("L", (s, s), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, s - 1, s - 1], radius=radius, fill=255)
    base_img = _gradient(s, c["bg_top"], c["bg_bottom"]).convert("RGBA")  # type: ignore[arg-type]
    img.paste(base_img, (0, 0), mask)

    d = ImageDraw.Draw(img)

    # 1b) 浅灰外框（白底版本才需要，保证在白色桌面上仍看得见边界）
    if c["outline_bg"]:
        d.rounded_rectangle([0, 0, s - 1, s - 1], radius=radius,
                            outline=c["outline_bg"] + (255,), width=max(int(0.012 * s), 1))  # type: ignore[operator]

    # 2) 显示器外框（深蓝描边 + 白色屏面）
    stroke = max(int(0.052 * s), 2)
    panel = [int(0.155 * s), int(0.195 * s), int(0.845 * s), int(0.655 * s)]
    d.rounded_rectangle(panel, radius=int(0.055 * s), fill=c["panel"] + (255,),  # type: ignore[operator]
                        outline=c["edge"] + (255,), width=stroke)               # type: ignore[operator]

    # 3) 屏幕里的月牙（息屏的含义）
    moon_box = (int(0.40 * s), int(0.29 * s), int(0.625 * s), int(0.515 * s))
    cut_box = (int(0.485 * s), int(0.245 * s), int(0.70 * s), int(0.46 * s))
    moon_mask = ImageChops.subtract(_ell(moon_box, s), _ell(cut_box, s))
    img.paste(Image.new("RGBA", (s, s), c["moon"] + (255,)), (0, 0), moon_mask)  # type: ignore[operator]

    # 4) 底座：竖颈 + 横底座
    neck = [int(0.455 * s), int(0.655 * s), int(0.545 * s), int(0.755 * s)]
    base = [int(0.325 * s), int(0.755 * s), int(0.675 * s), int(0.815 * s)]
    d.rectangle(neck, fill=c["edge"] + (255,))                                   # type: ignore[operator]
    d.rounded_rectangle(base, radius=int(0.018 * s), fill=c["edge"] + (255,))    # type: ignore[operator]

    # 5) 底座下沿一点环境光，让图标有"息屏微光"的感觉
    glow_h = max(int(0.02 * s), 1)
    d.rounded_rectangle([int(0.36 * s), int(0.815 * s), int(0.64 * s), int(0.815 * s) + glow_h],
                        radius=glow_h, fill=c["glow"] + (150,))                  # type: ignore[operator]

    return img.resize((size, size), Image.LANCZOS)


def main() -> int:
    ap = argparse.ArgumentParser(description="生成「关闭屏幕」工具图标")
    ap.add_argument("--out", default=None, help="输出目录，默认脚本所在目录")
    ap.add_argument("--theme", default="light", choices=sorted(THEMES),
                    help="配色方案：light=纯白底（默认），dark=深蓝渐变底")
    args = ap.parse_args()

    out_dir = Path(args.out) if args.out else Path(__file__).resolve().parent
    out_dir.mkdir(parents=True, exist_ok=True)

    images = [render(sz, args.theme) for sz in SIZES]
    ico_path = out_dir / "关闭屏幕.ico"
    images[0].save(ico_path, format="ICO",
                   sizes=[(im.width, im.height) for im in images])
    png_path = out_dir / "图标预览.png"
    images[0].save(png_path)

    # 另外把两套主题都导出成独立命名的 ico（命名不同 = 图标缓存不会串，
    # 桌面快捷方式换主题时只要改指向的文件名即可立刻生效）
    for t in sorted(THEMES):
        imgs_t = [render(sz, t) for sz in SIZES]
        p = out_dir / f"图标-{t}.ico"
        imgs_t[0].save(p, format="ICO", sizes=[(im.width, im.height) for im in imgs_t])
        print(f"[完成] {t} 主题 ico：{p}")

    # 附一张"各尺寸并排"的对照图，方便肉眼确认小尺寸是否清楚
    w = sum(SIZES) + 20 * (len(SIZES) + 1)
    sheet = Image.new("RGBA", (w, 296), SHEET_BG + (255,))
    x = 20
    for im in images:
        sheet.paste(im, (x, 20 + (256 - im.height) // 2), im)
        x += im.width + 20
    sheet_path = out_dir / "图标尺寸对照.png"
    sheet.save(sheet_path)

    print(f"[完成] 配色：{args.theme}")
    print(f"[完成] ICO：{ico_path}（含 {', '.join(str(s) for s in SIZES)} 六种尺寸）")
    print(f"[完成] 预览：{png_path}")
    print(f"[完成] 尺寸对照：{sheet_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
