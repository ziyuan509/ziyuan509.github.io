#!/usr/bin/env python3
"""
把品牌标识处理成站点要用的浅色/深色两版。

    python tools/make_logo_variants.py

源文件放 sources/logos/，产出到 assets/img/logos/：
    <name>.png        浅色主题用（原色）
    <name>-dark.png   深色主题用（反白版）

为什么要单独做一份反白版而不是用 CSS filter：
filter 是整体运算，做不到「只把深色文字翻白、红色图形保持不变」。
品牌方的官方反白版通常正是这种混合处理，所以按同样的规则生成。

reverse 模式：
    all      整个标识都翻成白色（单色标，如腾讯蓝字标）
    neutral  只把接近中性的深色部分翻白，保留饱和色
             （如网易互娱：红色火焰保留，深灰文字翻白）
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "sources" / "logos"
OUT = ROOT / "assets" / "img" / "logos"

MAX_W = 900          # 页面上只显示 56px 宽，900 足够 retina 用了
NEUTRAL_SAT = 40     # max-min 小于这个值算中性色

# 输出名 -> (源文件, reverse 模式)
JOBS = {
    "tencent":       ("03_Tencent_English-logo.png", "all"),
    "netease-games": ("OBT-LOGO.webp",               "neutral"),
}


def trim(im: Image.Image) -> Image.Image:
    """裁掉四周全透明的边，让标识填满画布——否则在小格子里会白白缩水。"""
    bbox = im.getchannel("A").getbbox()
    return im.crop(bbox) if bbox else im


def limit(im: Image.Image, w: int) -> Image.Image:
    if im.width <= w:
        return im
    return im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)


def reverse(im: Image.Image, mode: str) -> Image.Image:
    """生成反白版：保留 alpha，按模式把颜色改成白色。"""
    out = im.copy()
    px = out.load()
    w, h = out.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            if mode == "all":
                px[x, y] = (255, 255, 255, a)
            else:  # neutral：只翻中性深色，饱和色原样保留
                if max(r, g, b) - min(r, g, b) < NEUTRAL_SAT:
                    px[x, y] = (255, 255, 255, a)
    return out


def main() -> int:
    if not SRC.exists():
        print(f"! 找不到 {SRC}", file=sys.stderr)
        return 1
    OUT.mkdir(parents=True, exist_ok=True)

    for name, (fname, mode) in JOBS.items():
        p = SRC / fname
        if not p.exists():
            print(f"! 缺 {fname}", file=sys.stderr)
            continue

        im = limit(trim(Image.open(p).convert("RGBA")), MAX_W)
        light = OUT / f"{name}.png"
        im.save(light, optimize=True)

        dark = OUT / f"{name}-dark.png"
        reverse(im, mode).save(dark, optimize=True)

        print(f"  {name:16} {im.width}×{im.height}  比例 {im.width/im.height:.2f}  "
              f"浅 {light.stat().st_size/1024:5.1f} KB / 深 {dark.stat().st_size/1024:5.1f} KB  "
              f"(reverse={mode})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
