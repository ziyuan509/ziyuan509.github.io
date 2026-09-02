#!/usr/bin/env python3
"""
把 Google Fonts 的字体文件抓到本地自托管。

为什么要这么做：fonts.googleapis.com 在中国大陆基本不通，靠 CDN 引字体的话，
大陆访客（包括你自己）看到的是系统默认字体，整套排版设计等于没有。
自托管之后全站零外部请求，任何网络环境下表现一致，也更快。

    python tools/fetch_fonts.py

产出：
    assets/fonts/*.woff2    字体文件
    assets/css/fonts.css    @font-face 声明，由 build.py 引入

重跑会覆盖。想换字体就改下面的 FAMILIES，重跑，再改 main.css 里的 --display/--sans。
"""

from __future__ import annotations

import re
import sys
import urllib.request
from pathlib import Path

for _s in (sys.stdout, sys.stderr):          # Windows 重定向时避免 GBK 编码错误
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
FONT_DIR = ROOT / "assets" / "fonts"
CSS_OUT = ROOT / "assets" / "css" / "fonts.css"

# 现代浏览器 UA 才能拿到 woff2（老 UA 会返回体积大得多的 ttf）
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

# 用字重区间请求，拿到的是可变字体：一个文件覆盖所有字重，比每个字重一个文件小得多
FAMILIES = [
    "Schibsted Grotesk:wght@400..700",
    "Figtree:wght@400..700",
    "JetBrains Mono:wght@400..500",
]

# 站点是英文的，中文由系统字体兜底，所以只要拉丁字符集
KEEP_SUBSETS = {"latin", "latin-ext"}


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return urllib.request.urlopen(req, timeout=30).read()


def main() -> int:
    FONT_DIR.mkdir(parents=True, exist_ok=True)

    query = "&".join("family=" + f.replace(" ", "+") for f in FAMILIES)
    url = f"https://fonts.googleapis.com/css2?{query}&display=swap"
    print(f"→ {url}")

    try:
        css = fetch(url).decode("utf-8")
    except Exception as exc:
        print(f"! 拉取 CSS 失败：{exc}", file=sys.stderr)
        return 1

    # Google 返回的 CSS 形如：/* latin */ @font-face { ... }
    blocks = re.findall(r"/\*\s*([\w-]+)\s*\*/\s*(@font-face\s*\{[^}]+\})", css)
    if not blocks:
        print("! 没解析出 @font-face，Google 可能改了返回格式", file=sys.stderr)
        return 1

    out, seen, total = [], set(), 0
    for subset, block in blocks:
        if subset not in KEEP_SUBSETS:
            continue

        m = re.search(r"url\((https://[^)]+\.woff2)\)", block)
        if not m:
            continue
        remote = m.group(1)

        family = re.search(r"font-family:\s*'([^']+)'", block).group(1)
        weight = re.search(r"font-weight:\s*([^;]+);", block).group(1).strip()

        name = f"{family.lower().replace(' ', '-')}-{subset}.woff2"
        dest = FONT_DIR / name

        if name not in seen:
            data = fetch(remote)
            dest.write_bytes(data)
            total += len(data)
            seen.add(name)
            print(f"  {name:<34} {len(data)/1024:6.1f} KB  ({family} {weight}, {subset})")

        local = block.replace(remote, f"../fonts/{name}")
        out.append(f"/* {family} · {subset} */\n{local}")

    if not out:
        print("! 一个字体都没下到", file=sys.stderr)
        return 1

    header = (
        "/* 自动生成，请勿手改 —— 重新生成：python tools/fetch_fonts.py\n"
        "   自托管字体：不依赖 fonts.googleapis.com，大陆可正常访问。 */\n\n"
    )
    CSS_OUT.write_text(header + "\n\n".join(out) + "\n", encoding="utf-8")

    print(f"\n✓ {len(seen)} 个字体文件，合计 {total/1024:.1f} KB")
    print(f"✓ {CSS_OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
