#!/usr/bin/env python3
"""
生成社交分享图（og:image）和 iOS 主屏图标。

    python tools/make_og.py

产出：
    assets/img/og.png                1200×630，分享到微信/Slack/Twitter 时的预览图
    assets/img/apple-touch-icon.png  180×180，iOS 添加到主屏时的图标

配色和字体都跟站点一致，直角、无圆角。改了 data/site.toml 里的姓名或身份之后重跑即可。
想用自己设计的图，直接覆盖 assets/img/og.png，别跑这个脚本就行。

TTF 从 Google Fonts 取（用裸 UA 才会返回 ttf，woff2 Pillow 读不了），
缓存在 tools/.fontcache/，已在 .gitignore 里，不会进仓库。
"""

from __future__ import annotations

import sys
import tomllib
import urllib.request
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("! 需要 Pillow：pip install pillow", file=sys.stderr)
    sys.exit(1)

for _s in (sys.stdout, sys.stderr):          # Windows 重定向时避免 GBK 编码错误
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
CACHE = Path(__file__).resolve().parent / ".fontcache"
IMG_DIR = ROOT / "assets" / "img"

# 跟 main.css 的 token 保持一致
BG      = (252, 251, 253)
INK     = (26, 23, 32)
MUTED   = (107, 100, 120)
ACCENT  = (106, 61, 168)
RULE    = (229, 226, 236)
ON_DARK = (255, 255, 255)

UA_TTF = "Mozilla/5.0"   # 裸 UA → Google 返回 ttf


def ttf(family: str, weight: int) -> Path:
    """取一个字重的 TTF，带本地缓存。"""
    CACHE.mkdir(exist_ok=True)
    dest = CACHE / f"{family.lower().replace(' ', '-')}-{weight}.ttf"
    if dest.exists():
        return dest

    css_url = (f"https://fonts.googleapis.com/css2?"
               f"family={family.replace(' ', '+')}:wght@{weight}")
    req = urllib.request.Request(css_url, headers={"User-Agent": UA_TTF})
    css = urllib.request.urlopen(req, timeout=30).read().decode()

    import re
    m = re.search(r"url\((https://[^)]+\.ttf)\)", css)
    if not m:
        raise RuntimeError(f"没拿到 {family} {weight} 的 ttf")
    dest.write_bytes(urllib.request.urlopen(
        urllib.request.Request(m.group(1), headers={"User-Agent": UA_TTF}), timeout=30).read())
    print(f"  cached {dest.name}")
    return dest


def tracked(draw, xy, text, font, fill, tracking=0.0):
    """Pillow 没有字距控制，逐字画。tracking 单位是 px，可为负。"""
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        x += draw.textlength(ch, font=font) + tracking
    return x


def text_width(draw, text, font, tracking=0.0):
    return sum(draw.textlength(c, font=font) for c in text) + tracking * max(len(text) - 1, 0)


def main() -> int:
    with (ROOT / "data" / "site.toml").open("rb") as f:
        site = tomllib.load(f)["site"]

    name = site["name"]
    role = site.get("role", "")
    aff = site.get("affiliation", "")
    url = (site.get("url") or "").replace("https://", "").replace("http://", "").rstrip("/")

    IMG_DIR.mkdir(parents=True, exist_ok=True)

    try:
        f_name = ImageFont.truetype(str(ttf("Schibsted Grotesk", 700)), 92)
        f_role = ImageFont.truetype(str(ttf("Figtree", 400)), 34)
        f_mono = ImageFont.truetype(str(ttf("JetBrains Mono", 400)), 24)
        f_mark = ImageFont.truetype(str(ttf("Schibsted Grotesk", 700)), 92)
    except Exception as exc:
        print(f"! 字体获取失败：{exc}", file=sys.stderr)
        return 1

    # ---- og.png ----------------------------------------------------------
    W, H, PAD, BAR = 1200, 630, 88, 14
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)

    # 左侧竖条，跟站点用直线做重音的语言一致
    d.rectangle([0, 0, BAR, H], fill=ACCENT)

    # 文字块整体垂直居中；域名那行只在填了 url 时才画，
    # 否则底部会留一条没有内容的悬空细线。
    lines = [l for l in (role, aff) if l]
    block_h = 118 + 50 * len(lines) - (50 - 38 if lines else 0)
    y = (H - block_h) // 2 - 10

    tracked(d, (PAD + BAR, y), name, f_name, INK, tracking=-2.4)
    y += 118
    for line in lines:
        d.text((PAD + BAR, y), line, font=f_role, fill=MUTED)
        y += 50

    if url:
        d.rectangle([PAD + BAR, H - PAD - 54, W - PAD, H - PAD - 53], fill=RULE)
        tracked(d, (PAD + BAR, H - PAD - 34), url, f_mono, ACCENT, tracking=1.2)

    im.save(IMG_DIR / "og.png", optimize=True)
    print(f"✓ assets/img/og.png  {W}×{H}  "
          f"{(IMG_DIR / 'og.png').stat().st_size / 1024:.1f} KB")

    # ---- apple-touch-icon.png -------------------------------------------
    # 字号自适应：让首字母占画布宽度的 ~56%，四周留出呼吸空间；
    # 垂直方向按实际墨迹外框（含 Q 这类下降部）居中，不靠基线估。
    S = 180
    initials = "".join(w[0] for w in name.split()[:2]).upper() or "?"
    icon = Image.new("RGB", (S, S), ACCENT)
    di = ImageDraw.Draw(icon)

    size, track = 80, -3
    for _ in range(12):
        f_icon = ImageFont.truetype(str(ttf("Schibsted Grotesk", 700)), size)
        w = text_width(di, initials, f_icon, track)
        if w <= S * 0.56:
            break
        size -= 3
    f_icon = ImageFont.truetype(str(ttf("Schibsted Grotesk", 700)), size)

    w = text_width(di, initials, f_icon, track)
    bbox = di.textbbox((0, 0), initials, font=f_icon)
    tracked(di, ((S - w) / 2, (S - (bbox[3] - bbox[1])) / 2 - bbox[1]),
            initials, f_icon, ON_DARK, tracking=track)
    icon.save(IMG_DIR / "apple-touch-icon.png", optimize=True)
    print(f"✓ assets/img/apple-touch-icon.png  {S}×{S}  "
          f"{(IMG_DIR / 'apple-touch-icon.png').stat().st_size / 1024:.1f} KB")

    return 0


if __name__ == "__main__":
    sys.exit(main())
