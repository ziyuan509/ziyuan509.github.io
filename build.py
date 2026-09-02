#!/usr/bin/env python3
"""
Per-Website 静态站生成器
========================

零第三方依赖：数据用 TOML（Python 3.11+ 自带 tomllib），模板就是下面这些
Python 函数。检测到 `markdown` 包会用它渲染文章，没有就走内置的精简解析器。

    python build.py            生成到 docs/
    python build.py --serve    生成后起一个本地服务器

输出目录 docs/ 可以直接作为 GitHub Pages 的源（Settings → Pages →
Deploy from a branch → main / docs）。
"""

from __future__ import annotations

import hashlib
import html
import re
import shutil
import sys
import tomllib
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

# Windows 上 stdout 被重定向时，Python 默认走系统 ANSI 代码页（中文环境是 GBK），
# 输出里的 ✓ 会直接抛 UnicodeEncodeError。CI 和日志重定向都会踩到，这里强制 UTF-8。
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
CONTENT = ROOT / "content"
ASSETS = ROOT / "assets"
OUT = ROOT / "docs"

# 导航栏全量定义。想换成中文标签，改这里的第一个元素即可。
NAV = [
    ("about", "index.html"),
    ("publications", "publications.html"),
    ("projects", "projects.html"),
    ("cv", "cv.html"),
    ("notes", "notes.html"),
    ("games", "games.html"),
]

# 实际渲染用的导航。main() 会把没有内容的栏目（notes / games）剔掉——
# 空页面挂在导航里只会让人白点一次。往 content/posts/ 或 games.toml
# 加了内容之后，页面和导航项会自动回来，不用改代码。
NAV_ACTIVE: list[tuple[str, str]] = list(NAV)

BASE = ""  # 由 site.toml 的 base_url 覆盖

# CSS/JS 的内容指纹。浏览器会按 GitHub Pages 给的 max-age=600 缓存这些文件，
# 改了样式之后回访的人可能十分钟内还看到旧版。带上内容哈希后，
# 文件一变 URL 就变，缓存立即失效。
ASSET_V: dict[str, str] = {}


def stamp(rel: str) -> str:
    """给站内静态资源加上内容哈希查询串。"""
    path = ROOT / rel.lstrip("/")
    if not path.exists():
        return u(rel)
    key = ASSET_V.get(rel)
    if key is None:
        key = hashlib.sha1(path.read_bytes()).hexdigest()[:8]
        ASSET_V[rel] = key
    return f"{u(rel)}?v={key}"


# ── 工具 ──────────────────────────────────────────────────────────────────

def load(name: str) -> dict:
    path = DATA / name
    if not path.exists():
        return {}
    with path.open("rb") as f:
        return tomllib.load(f)


def e(s) -> str:
    """转义。用于确定不含 HTML 的字段。"""
    return html.escape(str(s), quote=True)


def u(path: str) -> str:
    """站内绝对路径，自动加上 base_url 前缀。"""
    if re.match(r"^(https?:|mailto:|#|//)", path):
        return path
    return (BASE + "/" + path.lstrip("/")) if BASE else "/" + path.lstrip("/")


def has_asset(rel: str) -> bool:
    return bool(rel) and (ROOT / rel.lstrip("/")).exists()


def slugify(s: str) -> str:
    s = re.sub(r"[^\w一-鿿\- ]+", "", s).strip().lower()
    return re.sub(r"[\s_]+", "-", s) or "item"


# ── 图标 ──────────────────────────────────────────────────────────────────
# 统一 24×24 视框。除 GitHub 用官方描摹路径外，其余是同一套线性图标，
# 保证整排图标的视觉重量一致。想换成品牌原生 logo，替换对应条目即可。

_S = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
      'stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" '
      'aria-hidden="true">{}</svg>')
_F = '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">{}</svg>'

ICONS = {
    "email": _S.format(
        '<rect x="2.5" y="5" width="19" height="14" rx="2.5"/><path d="M3.2 7.2 12 13l8.8-5.8"/>'),
    "scholar": _S.format(
        '<path d="M12 4 2.5 9 12 14l9.5-5L12 4Z"/><path d="M6.5 11.3V16c0 1.7 2.5 3 5.5 3s5.5-1.3 5.5-3v-4.7"/>'
        '<path d="M21.5 9v5"/>'),
    # 官方 mark 路径，务必保持在一行——跨行拼接会吞掉分段之间的空格
    "github": _F.format(
        '<path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12"/>'),
    "orcid": ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true">'
              '<circle cx="12" cy="12" r="9.2"/>'
              '<text x="12" y="16.1" text-anchor="middle" font-size="9.4" font-weight="700" '
              'font-family="system-ui,sans-serif" fill="currentColor" stroke="none">iD</text></svg>'),
    "arxiv": _S.format(
        '<path d="M6 3.2h7.5L19 8.7V20a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V4.2a1 1 0 0 1 1-1Z"/>'
        '<path d="M13.3 3.4v5.4h5.4"/><path d="M8.6 13.2l5 5M13.6 13.2l-5 5"/>'),
    "dblp": _S.format(
        '<ellipse cx="12" cy="6.2" rx="7.2" ry="2.9"/><path d="M4.8 6.2v5.6c0 1.6 3.2 2.9 7.2 2.9s7.2-1.3 7.2-2.9V6.2"/>'
        '<path d="M4.8 11.8v5.6c0 1.6 3.2 2.9 7.2 2.9s7.2-1.3 7.2-2.9v-5.6"/>'),
    "cv": _S.format(
        '<path d="M6 3.2h7.5L19 8.7V20a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V4.2a1 1 0 0 1 1-1Z"/>'
        '<path d="M13.3 3.4v5.4h5.4"/><path d="M8.4 13.4h7.2M8.4 16.6h5"/>'),
    "twitter": _S.format('<path d="M4 4l7.6 9.6L4.4 20M20 4l-7.4 8.2L20 20h-3.4L4 4h3.6"/>'),
    "bluesky": _S.format(
        '<path d="M12 10.6C10.5 7.6 6.9 4 4.8 4 3.2 4 2.7 5.3 2.7 6.8c0 1.6.7 5.4 1.2 6.3.8 1.5 2.4 1.8 4 1.6'
        '-2.6.4-3.3 1.9-2 3.4 2.5 2.8 4.6-1.5 5.1-3 .5 1.5 2.6 5.8 5.1 3 1.3-1.5.6-3-2-3.4 1.6.2 3.2-.1 4-1.6'
        '.5-.9 1.2-4.7 1.2-6.3 0-1.5-.5-2.8-2.1-2.8-2.1 0-5.7 3.6-7.2 6.6Z"/>'),
    "mastodon": _S.format(
        '<path d="M12 3.2c4.4 0 7.2 1.4 7.2 5.4 0 3.3.3 6.4-2.6 7.2-1.6.4-3.2.5-4.6.4"/>'
        '<path d="M12 3.2C7.6 3.2 4.8 4.6 4.8 8.6c0 5.3-.3 9.6 7.2 11.4 2.6.6 4.9.4 6.6-.5"/>'
        '<path d="M8.6 12.6V9.4a1.7 1.7 0 0 1 3.4 0v2M12 9.4a1.7 1.7 0 0 1 3.4 0v3.2"/>'),
    "linkedin": ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true">'
                 '<rect x="3" y="3" width="18" height="18" rx="3.4"/>'
                 '<text x="12" y="16.1" text-anchor="middle" font-size="9" font-weight="700" '
                 'font-family="system-ui,sans-serif" fill="currentColor" stroke="none">in</text></svg>'),
    "youtube": _S.format(
        '<rect x="2.4" y="5.4" width="19.2" height="13.2" rx="3.6"/><path d="M10.4 9.4l5 2.6-5 2.6V9.4Z"/>'),
    "itch": _S.format(
        '<path d="M3.2 7.4 5.6 4h12.8l2.4 3.4"/><path d="M3.2 7.4V19a1 1 0 0 0 1 1h15.6a1 1 0 0 0 1-1V7.4"/>'
        '<path d="M9 12.2h6M12 9.4v5.6"/>'),
    "instagram": _S.format(
        '<rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/>'
        '<circle cx="17.2" cy="6.8" r="1.1" fill="currentColor" stroke="none"/>'),
    "rss": _S.format('<path d="M5 11.4A7.6 7.6 0 0 1 12.6 19M5 5.6A13.4 13.4 0 0 1 18.4 19"/>'
                     '<circle cx="5.6" cy="18.4" r="1.4" fill="currentColor" stroke="none"/>'),
}

ICON_LABEL = {
    "email": "Email", "scholar": "Google Scholar", "github": "GitHub", "orcid": "ORCID",
    "arxiv": "arXiv", "dblp": "DBLP", "cv": "CV (PDF)", "twitter": "X / Twitter",
    "bluesky": "Bluesky", "mastodon": "Mastodon", "linkedin": "LinkedIn",
    "youtube": "YouTube", "itch": "itch.io", "instagram": "Instagram", "rss": "RSS",
}

THEME_ICONS = (
    '<span data-icon="system">' + _S.format(
        '<rect x="2.6" y="4" width="18.8" height="12.4" rx="2"/><path d="M8.4 20h7.2M12 16.6V20"/>') + '</span>'
    '<span data-icon="light">' + _S.format(
        '<circle cx="12" cy="12" r="4"/><path d="M12 2.6v2.2M12 19.2v2.2M2.6 12h2.2M19.2 12h2.2'
        'M5.4 5.4l1.6 1.6M17 17l1.6 1.6M18.6 5.4 17 7M7 17l-1.6 1.6"/>') + '</span>'
    '<span data-icon="dark">' + _S.format(
        '<path d="M20.4 13.6A8.4 8.4 0 1 1 10.4 3.6a6.6 6.6 0 0 0 10 10Z"/>') + '</span>'
)

# 详情页 facts 用的大号线性图标。统一 24 视框、1.4 描边，
# 在 32px 上显示时线条不会糊。
_L = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" '
      'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{}</svg>')

FACT_ICONS = {
    "place":    _L.format('<path d="M12 21.5s7-5.6 7-11a7 7 0 1 0-14 0c0 5.4 7 11 7 11Z"/>'
                          '<circle cx="12" cy="10.2" r="2.6"/>'),
    "sensing":  _L.format('<circle cx="12" cy="12" r="2"/><path d="M8.2 8.2a5.4 5.4 0 0 0 0 7.6"/>'
                          '<path d="M15.8 15.8a5.4 5.4 0 0 0 0-7.6"/>'
                          '<path d="M5.4 5.4a9.4 9.4 0 0 0 0 13.2"/><path d="M18.6 18.6a9.4 9.4 0 0 0 0-13.2"/>'),
    "hardware": _L.format('<rect x="7" y="7" width="10" height="10" rx="1"/>'
                          '<path d="M10 3.5v3M14 3.5v3M10 17.5v3M14 17.5v3'
                          'M3.5 10h3M3.5 14h3M17.5 10h3M17.5 14h3"/>'),
    "code":     _L.format('<path d="M8.6 8.4 4.6 12l4 3.6M15.4 8.4l4 3.6-4 3.6M13.6 5.4l-3.2 13.2"/>'),
    "people":   _L.format('<circle cx="9" cy="8.4" r="3.2"/><path d="M3.4 19.6a5.6 5.6 0 0 1 11.2 0"/>'
                          '<path d="M16.2 6a3.2 3.2 0 0 1 0 6.4M17.4 15.2a5.6 5.6 0 0 1 3.2 4.4"/>'),
    "layers":   _L.format('<path d="m12 3.2 8.4 4.4-8.4 4.4-8.4-4.4L12 3.2Z"/>'
                          '<path d="m3.6 12 8.4 4.4 8.4-4.4M3.6 16.4 12 20.8l8.4-4.4"/>'),
    "time":     _L.format('<circle cx="12" cy="12" r="8.6"/><path d="M12 6.8V12l3.4 2"/>'),
    "display":  _L.format('<rect x="2.6" y="4.4" width="18.8" height="12.6" rx="1.4"/>'
                          '<path d="M8.4 20.6h7.2M12 17.2v3.4"/>'),
    "hand":     _L.format('<path d="M8.4 11V5.6a1.6 1.6 0 0 1 3.2 0V11"/>'
                          '<path d="M11.6 10.6V4.4a1.6 1.6 0 0 1 3.2 0v6.2"/>'
                          '<path d="M14.8 11V7.2a1.6 1.6 0 0 1 3.2 0v7.4a6 6 0 0 1-6 6h-1a5 5 0 0 1-3.6-1.5l-3-3.1'
                          'a1.6 1.6 0 0 1 2.3-2.3l1.7 1.6"/>'),
}

MONTHS = ["January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December"]

MENU_ICON = _S.format('<path d="M4 7h16M4 12h16M4 17h16"/>')


# ── Markdown ──────────────────────────────────────────────────────────────

def md_to_html(text: str) -> str:
    try:
        import markdown as _md  # 可选依赖，装了就用
        return _md.markdown(text, extensions=["extra", "sane_lists"])
    except ImportError:
        return _mini_md(text)


def _inline(s: str) -> str:
    holds: list[str] = []

    def hold(m):
        holds.append(m.group(1))
        return "\x00%d\x00" % (len(holds) - 1)

    s = re.sub(r"`([^`]+)`", hold, s)
    s = re.sub(r"!\[([^\]]*)\]\(([^)\s]+)\)", r'<img src="\2" alt="\1">', s)
    s = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2">\1</a>', s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])", r"<em>\1</em>", s)
    s = re.sub(r"\x00(\d+)\x00",
               lambda m: "<code>" + html.escape(holds[int(m.group(1))]) + "</code>", s)
    return s


def _mini_md(text: str) -> str:
    out: list[str] = []
    para: list[str] = []
    state = {"list": None}
    lines = text.replace("\r\n", "\n").split("\n")

    def flush():
        if para:
            out.append("<p>" + _inline(" ".join(para).strip()) + "</p>")
            para.clear()

    def close_list():
        if state["list"]:
            out.append("</%s>" % state["list"])
            state["list"] = None

    i = 0
    while i < len(lines):
        st = lines[i].strip()

        if st.startswith("```"):
            flush(); close_list()
            i += 1
            buf = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                buf.append(lines[i]); i += 1
            i += 1
            out.append("<pre><code>" + html.escape("\n".join(buf)) + "</code></pre>")
            continue

        if not st:
            flush(); close_list(); i += 1; continue

        m = re.match(r"^(#{1,4})\s+(.*)$", st)
        if m:
            flush(); close_list()
            lvl = len(m.group(1))
            out.append("<h%d>%s</h%d>" % (lvl, _inline(m.group(2)), lvl))
            i += 1; continue

        if re.match(r"^(-{3,}|\*{3,}|_{3,})$", st):
            flush(); close_list(); out.append("<hr>"); i += 1; continue

        if st.startswith(">"):
            flush(); close_list()
            buf = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                buf.append(lines[i].strip().lstrip(">").strip()); i += 1
            out.append("<blockquote><p>" + _inline(" ".join(buf)) + "</p></blockquote>")
            continue

        m = re.match(r"^[-*+]\s+(.*)$", st)
        if m:
            flush()
            if state["list"] != "ul":
                close_list(); out.append("<ul>"); state["list"] = "ul"
            out.append("<li>" + _inline(m.group(1)) + "</li>")
            i += 1; continue

        m = re.match(r"^\d+[.)]\s+(.*)$", st)
        if m:
            flush()
            if state["list"] != "ol":
                close_list(); out.append("<ol>"); state["list"] = "ol"
            out.append("<li>" + _inline(m.group(1)) + "</li>")
            i += 1; continue

        para.append(st)
        i += 1

    flush(); close_list()
    return "\n".join(out)


# ── 页面外壳 ──────────────────────────────────────────────────────────────

# 防止深色模式下的白屏闪烁：在 CSS 之前同步执行
ANTI_FLASH = (
    "<script>document.documentElement.classList.add('js');(function(){try{var t=localStorage.getItem('pw-theme');"
    "if(t==='light'||t==='dark')document.documentElement.setAttribute('data-theme',t);}catch(e){}})();</script>"
)

ACCENT = "#6a3da8"   # 与 main.css 的 --accent 保持一致；改配色时两边一起改


def shell(site: dict, *, title: str, active: str, body: str,
          desc: str = "", path: str | None = None) -> str:
    full_title = title if title == site["name"] else f"{title} · {site['name']}"
    description = desc or site.get("description", "")
    links = []
    for label, href in NAV_ACTIVE:
        cur = ' aria-current="page"' if href == active else ""
        links.append(f'<a href="{u(href)}"{cur}>{e(label)}</a>')

    # canonical / og:url / og:image 都需要绝对地址，site.url 没填就整体省略
    site_url = (site.get("url") or "").rstrip("/")
    head_extra = []
    if site_url:
        page = path if path is not None else active
        loc = f"{site_url}/{page}"
        if loc.endswith("/index.html"):
            loc = loc[: -len("index.html")]
        head_extra.append(f'<link rel="canonical" href="{e(loc)}">')
        head_extra.append(f'<meta property="og:url" content="{e(loc)}">')
        if has_asset("assets/img/og.png"):
            og = f"{site_url}/assets/img/og.png"
            head_extra.append(f'<meta property="og:image" content="{e(og)}">')
            head_extra.append('<meta name="twitter:card" content="summary_large_image">')
            head_extra.append(f'<meta name="twitter:image" content="{e(og)}">')

    icons = [f'<link rel="icon" href="{u("favicon.svg")}" type="image/svg+xml">']
    if has_asset("assets/img/apple-touch-icon.png"):
        icons.append(f'<link rel="apple-touch-icon" href="{u("assets/img/apple-touch-icon.png")}">')

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(full_title)}</title>
<meta name="description" content="{e(description)}">
<meta name="author" content="{e(site['name'])}">
<meta property="og:title" content="{e(full_title)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{e(site['name'])}">
{chr(10).join(head_extra)}
{chr(10).join(icons)}
{ANTI_FLASH}
<link rel="stylesheet" href="{stamp('assets/css/fonts.css')}">
<link rel="stylesheet" href="{stamp('assets/css/main.css')}">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>

<nav class="nav">
  <div class="nav__inner">
    <a class="nav__brand" href="{u('index.html')}">{e(site['name'])}</a>
    <button class="nav__menu" type="button" aria-expanded="false" aria-controls="navlinks" aria-label="Menu">{MENU_ICON}</button>
    <div class="nav__links" id="navlinks">
      {''.join(links)}
      <button class="theme-toggle" type="button" data-state="system" aria-label="Toggle theme">{THEME_ICONS}</button>
    </div>
  </div>
</nav>

<main id="main">
{body}
</main>

<footer class="foot">
  <div class="wrap wrap--wide foot__inner">
    <span>© {date.today().year} {e(site['name'])}</span>
    {f"<span>{e(site['footer_note'])}</span>" if site.get('footer_note') else ''}
    <span class="foot__updated">updated {date.today().isoformat()}</span>
  </div>
</footer>

<script src="{stamp('assets/js/site.js')}" defer></script>
</body>
</html>
"""


def page_head(label: str, title: str, note: str = "", extra: str = "") -> str:
    bits = [f'<header class="page-head"><span class="label">{e(label)}</span><h1>{e(title)}</h1>']
    if note:
        bits.append(f"<p>{note}</p>")
    if extra:
        bits.append(extra)
    bits.append("</header>")
    return "".join(bits)


# ── 组件 ──────────────────────────────────────────────────────────────────

def socials(site: dict) -> str:
    items = []
    for s in site.get("social", []):
        kind = s.get("kind", "")
        icon = ICONS.get(kind)
        if not icon:
            continue
        label = ICON_LABEL.get(kind, kind)
        items.append(
            f'<a href="{e(u(s["url"]))}" title="{e(label)}" aria-label="{e(label)}"'
            f'{" rel=\"me noopener\" target=\"_blank\"" if kind not in ("email", "cv") else ""}>{icon}</a>')
    return f'<div class="socials">{"".join(items)}</div>' if items else ""


def thumb(rel: str, letter: str, cls: str) -> str:
    if has_asset(rel):
        return f'<img class="{cls}" src="{e(u(rel))}" alt="" loading="lazy">'
    return f'<div class="{cls} {cls}--empty" aria-hidden="true">{e(letter[:1].upper())}</div>'


def author_line(authors: list[str], me: str) -> str:
    parts = [f"<b>{e(a)}</b>" if a.strip() == me.strip() else e(a) for a in authors]
    return ", ".join(parts)


def pill_links(links: dict) -> str:
    return "".join(
        f'<a class="pill" href="{e(u(v))}"{" target=\"_blank\" rel=\"noopener\"" if v.startswith("http") else ""}>{e(k)}</a>'
        for k, v in links.items() if v)


def pub_entry(p: dict, me: str) -> str:
    links = p.get("links", {}) or {}
    award = f'<span class="award">{e(p["award"])}</span>' if p.get("award") else ""
    venue_full = p.get("venue_full", "")
    venue = (f'<em title="{e(venue_full)}">{e(p.get("venue", ""))}</em>' if venue_full
             else f'<em>{e(p.get("venue", ""))}</em>')

    # 切换钮留在按钮行里，抽屉放到行外面——靠 :has() 联动。
    # 抽屉如果留在 <details> 内部，展开时会把整行挤散，按钮位置会跳。
    toggles, drawers = [], []
    if p.get("abstract"):
        toggles.append('<details class="tgl tgl--abs">'
                       '<summary><span class="pill">abs</span></summary></details>')
        drawers.append(f'<div class="drawer drawer--abs">{e(p["abstract"].strip())}</div>')
    if p.get("bibtex"):
        toggles.append('<details class="tgl tgl--bib">'
                       '<summary><span class="pill">bib</span></summary></details>')
        drawers.append('<div class="drawer drawer--bib">'
                       '<button class="copy-bib" type="button">copy</button>'
                       f'<pre>{e(p["bibtex"].strip())}</pre></div>')

    title_html = e(p["title"])
    if links.get("page") or links.get("pdf") or links.get("doi"):
        href = links.get("page") or links.get("pdf") or links.get("doi")
        title_html = f'<a href="{e(u(href))}">{title_html}</a>'

    when = e(p.get("year", ""))
    if p.get("month"):
        when = f'{MONTHS[int(p["month"]) - 1]} {when}'

    return f"""<article class="pub">
  {thumb(p.get("thumb", ""), p["title"], "pub__thumb")}
  <div>
    <h3 class="pub__title">{title_html}{award}</h3>
    <div class="pub__authors">{author_line(p.get("authors", []), me)}</div>
    <div class="pub__venue">{venue} · {when}</div>
    <div class="pub__act">
      <div class="pills">{pill_links(links)}{"".join(toggles)}</div>
      {"".join(drawers)}
    </div>
  </div>
</article>"""


def project_url(p: dict) -> str:
    """详情页地址。没写 slug 就从名字生成一个。"""
    return u(f"projects/{p.get('slug') or slugify(p['name'])}.html")


def project_card(p: dict) -> str:
    """列表页与首页共用的卡片。整张卡片指向详情页，外链留到详情页里。"""
    tags = "".join(f'<span class="tag">{e(t)}</span>' for t in p.get("tags", [])[:3])
    href = project_url(p)
    return f"""<article class="card">
  <a class="card__media-link" href="{href}" tabindex="-1" aria-hidden="true">
    {thumb(p.get("card") or p.get("image", ""), p["name"], "card__media")}
  </a>
  <div class="card__body">
    <h3 class="card__title"><a href="{href}">{e(p["name"])}</a></h3>
    <p class="card__desc">{e(p.get("tagline", ""))}</p>
    <div class="card__foot"><span class="tag">{e(p.get("year", ""))}</span>{tags}</div>
  </div>
</article>"""


def project_facts(p: dict) -> str:
    facts = p.get("facts", [])
    if not facts:
        return ""
    items = []
    for f in facts:
        icon = FACT_ICONS.get(f.get("icon", ""), FACT_ICONS["layers"])
        items.append(f'<div class="fact"><span class="fact__icon">{icon}</span>'
                     f'<span class="fact__label">{e(f.get("label", ""))}</span>'
                     f'<span class="fact__value">{e(f.get("value", ""))}</span></div>')
    return f'<div class="facts reveal">{"".join(items)}</div>'


def project_sections(p: dict) -> str:
    out = []
    for sec in p.get("section", []):
        media = ""
        cap = f'<figcaption>{e(sec["caption"])}</figcaption>' if sec.get("caption") else ""

        if sec.get("video") and has_asset(sec["video"]):
            poster = (f' poster="{e(u(sec["poster"]))}"'
                      if has_asset(sec.get("poster", "")) else "")
            # 自动循环播放的无声演示。开了「减少动效」的用户由 site.js 改成手动播放。
            media = (f'<figure class="psec__fig"><video src="{e(u(sec["video"]))}"{poster} '
                     f'autoplay muted loop playsinline preload="metadata"></video>{cap}</figure>')
        elif has_asset(sec.get("image", "")):
            media = (f'<figure class="psec__fig"><img src="{e(u(sec["image"]))}" alt="" '
                     f'loading="lazy">{cap}</figure>')

        code = ""
        if sec.get("code"):
            label = (f'<figcaption>{e(sec["code_lang"])}</figcaption>'
                     if sec.get("code_lang") else "")
            code = (f'<figure class="psec__code"><pre><code>{e(sec["code"].strip())}</code></pre>'
                    f'{label}</figure>')

        out.append(f'<section class="psec reveal"><h2>{e(sec.get("heading", ""))}</h2>'
                   f'<div class="psec__body">{sec.get("body", "").strip()}</div>'
                   f'{code}{media}</section>')
    return "".join(out)


def play_entry(g: dict) -> str:
    rating = "".join(f'<i class="{"on" if i < int(g.get("rating", 0)) else ""}"></i>' for i in range(5))
    tags = " · ".join(g.get("tags", []))
    lesson = ""
    if g.get("lesson"):
        lesson = f'<div class="play__lesson"><b>takeaway</b>{e(g["lesson"])}</div>'
    return f"""<article class="play">
  {thumb(g.get("cover", ""), g["title"], "play__cover")}
  <div>
    <div class="play__head">
      <span class="play__title">{e(g["title"])}</span>
      <span class="rating" role="img" aria-label="Rated {e(g.get("rating", 0))} out of 5">{rating}</span>
      <span class="play__meta">{e(g.get("platform", ""))} · {e(g.get("year", ""))} · played {e(g.get("played", ""))}{" · " + e(tags) if tags else ""}</span>
    </div>
    <div class="play__take">{e(g.get("take", "").strip())}</div>
    {lesson}
  </div>
</article>"""


# ── 文章 ──────────────────────────────────────────────────────────────────

def read_posts() -> list[dict]:
    posts = []
    d = CONTENT / "posts"
    if not d.exists():
        return posts
    for path in sorted(d.glob("*.md"), reverse=True):
        raw = path.read_text(encoding="utf-8")
        meta, body = {}, raw
        if raw.lstrip().startswith("---"):
            parts = raw.lstrip().split("---", 2)
            if len(parts) >= 3:
                for line in parts[1].strip().splitlines():
                    if ":" in line:
                        k, v = line.split(":", 1)
                        meta[k.strip()] = v.strip()
                body = parts[2]
        posts.append({
            "title": meta.get("title", path.stem),
            "date": meta.get("date", ""),
            "excerpt": meta.get("excerpt", ""),
            "tags": [t.strip() for t in meta.get("tags", "").split(",") if t.strip()],
            "slug": re.sub(r"^\d{4}-\d{2}-\d{2}-", "", path.stem),
            "html": md_to_html(body),
        })
    posts.sort(key=lambda p: p["date"], reverse=True)
    return posts


# ── 各页面 ────────────────────────────────────────────────────────────────

def render_index(site, pubs, projects, posts, news) -> str:
    me = site["name"]

    initials = "".join(w[0] for w in me.split()[:2]).upper() or "?"
    photo = (f'<img class="profile__photo" src="{e(u(site["photo"]))}" alt="{e(me)}">'
             if has_asset(site.get("photo", "")) else
             f'<div class="profile__photo profile__photo--empty" aria-hidden="true">{e(initials)}</div>')

    contact = []
    if site.get("email"):
        contact.append(f'<div><span>✉</span><a href="mailto:{e(site["email"])}">{e(site["email"])}</a></div>')
    if site.get("location"):
        contact.append(f'<div><span>◎</span><span>{e(site["location"])}</span></div>')

    bio = "".join(f"<p>{p}</p>" for p in site.get("bio", []))
    aff = (f'<a href="{e(site["affiliation_url"])}">{e(site["affiliation"])}</a>'
           if site.get("affiliation_url") else e(site.get("affiliation", "")))

    news_html = "".join(
        f'<div class="news__item"><div class="news__date">{e(n["date"])}</div>'
        f'<div class="news__body">{n["text"]}</div></div>'
        for n in news)

    sel = [p for p in pubs if p.get("selected")][:3]
    feat = [p for p in projects if p.get("featured")][:3]

    def section(title: str, more: str, inner: str, wrap_cls: str = "") -> str:
        """空的板块整块不渲染——首页宁可短，也不要一排只有标题的空壳。"""
        if not inner:
            return ""
        body = f'<div class="{wrap_cls}">{inner}</div>' if wrap_cls else inner
        return (f'<section class="section"><div class="section__head"><h2>{e(title)}</h2>'
                f'<a class="section__more" href="{u(more)}">All →</a></div>{body}</section>')

    pubs_html = "".join(pub_entry(p, me) for p in sel)
    proj_html = "".join(project_card(p) for p in feat)
    posts_html = "".join(
        f'<div class="post-item"><div class="post-item__date">{e(p["date"])}</div>'
        f'<div><div class="post-item__title"><a href="{u("notes/" + p["slug"] + ".html")}">{e(p["title"])}</a></div>'
        f'<div class="post-item__excerpt">{e(p["excerpt"])}</div></div></div>'
        for p in posts[:3])

    body = f"""<div class="wrap wrap--wide">
  <div class="profile">
    <aside class="profile__aside">
      {photo}
      <div class="profile__contact">{''.join(contact)}</div>
    </aside>
    <div class="profile__main">
      <h1 class="profile__name">{e(me)}{f'<span class="pronouns">{e(site["pronouns"])}</span>' if site.get("pronouns") else ''}</h1>
      <p class="profile__role">{e(site.get('role', ''))}{' · ' + aff if aff else ''}</p>
      <div class="profile__bio">{bio}</div>
      {socials(site)}
    </div>
  </div>

  {f'<section class="section"><div class="section__head"><h2>Research Interests</h2></div><div class="ri">{site["research_interests"].strip()}</div></section>' if site.get("research_interests", "").strip() else ''}
  {f'<section class="section"><div class="section__head"><h2>News</h2></div><div class="news">{news_html}</div></section>' if news_html else ''}
  {section("Selected Publications", "publications.html", pubs_html)}
  {section("Selected Projects", "projects.html", proj_html, "grid grid--3")}
  {section("Recent Notes", "notes.html", posts_html, "post-list")}
</div>"""
    return shell(site, title=me, active="index.html", body=body)


def render_publications(site, pubs) -> str:
    me = site["name"]
    years = sorted({p.get("year", 0) for p in pubs}, reverse=True)
    blocks = []
    for y in years:
        entries = [p for p in pubs if p.get("year") == y]
        blocks.append(f'<div class="year-head"><span>{e(y)}</span></div>'
                      + "".join(pub_entry(p, me) for p in entries))
    body = f"""<div class="wrap wrap--wide">
  {page_head("publications", "Publications",
             "%d papers. Entries marked <em>abs</em> / <em>bib</em> expand in place." % len(pubs))}
  {"".join(blocks) or '<p class="empty">No publications yet.</p>'}
</div>"""
    return shell(site, title="Publications", active="publications.html", body=body)


KIND_LABEL = {"installation": "Installation", "device": "Device", "game": "Game",
              "tool": "Tool", "research": "Research", "other": "Project"}


def render_projects(site, projects) -> str:
    """列表页：两列卡片，点进去看详情。"""
    order = ["installation", "device", "game", "tool", "research", "other"]
    names = {"installation": "Installations", "device": "Devices", "game": "Games",
             "tool": "Tools", "research": "Research", "other": "Other"}
    blocks = []
    for kind in order:
        items = [p for p in projects if p.get("kind", "other") == kind]
        if not items:
            continue
        blocks.append(f'<section class="section"><div class="section__head"><h2>{names[kind]}</h2></div>'
                      f'<div class="grid reveal">{"".join(project_card(p) for p in items)}</div></section>')
    body = f"""<div class="wrap wrap--wide">
  {page_head("projects", "Projects", "Installations, devices and games. Each one opens onto a fuller write-up.")}
  {"".join(blocks) or '<p class="empty">No projects yet.</p>'}
</div>"""
    return shell(site, title="Projects", active="projects.html", body=body)


def render_project(site, p) -> str:
    """单个作品的详情页。"""
    links = p.get("links", {}) or {}
    tags = "".join(f'<span class="tag">{e(t)}</span>' for t in p.get("tags", []))
    meta = " · ".join(x for x in (KIND_LABEL.get(p.get("kind", "other"), "Project"),
                                  str(p.get("year", "")), p.get("role", "")) if x)
    hero = ""
    if has_asset(p.get("image", "")):
        hero = (f'<div class="phero reveal"><img src="{e(u(p["image"]))}" alt=""></div>')
    pills = pill_links(links)

    body = f"""<div class="wrap wrap--wide">
  <a class="pfloat" href="{u('projects.html')}" aria-label="Back to all projects">
    {_S.format('<path d="M15 5 8 12l7 7"/>')}<span>Projects</span>
  </a>
  <p class="pback"><a href="{u('projects.html')}">← Projects</a></p>
  <header class="phead">
    <span class="label">{e(meta)}</span>
    <h1>{e(p["name"])}</h1>
    <p class="phead__lead">{p.get("lead", p.get("tagline", "")).strip()}</p>
    <div class="phead__foot">{tags}</div>
    {f'<div class="pills">{pills}</div>' if pills else ''}
  </header>
  {hero}
  {project_facts(p)}
  <div class="psecs">{project_sections(p)}</div>
  <p class="pback pback--end"><a href="{u('projects.html')}">← All projects</a></p>
</div>"""
    return shell(site, title=p["name"], active="projects.html", body=body,
                 desc=p.get("tagline", ""),
                 path=f"projects/{p.get('slug') or slugify(p['name'])}.html")


def render_cv(site, cv) -> str:
    blocks = []
    for sec in cv.get("section", []):
        entries = sec.get("entry", [])
        # 整个栏目里只要有一条带 logo，就给所有行加上 logo 列，保证左边缘对齐
        has_logo = any(has_asset(en.get("logo", "")) for en in entries)
        rows = []
        for en in entries:
            where = f'<span class="cv-row__where">{e(en["where"])}</span>' if en.get("where") else ""
            note = f'<div class="cv-row__note">{e(en["note"])}</div>' if en.get("note") else ""
            logo = ""
            if has_logo:
                inner = ""
                if has_asset(en.get("logo", "")):
                    if has_asset(en.get("logo_dark", "")):
                        # 有官方反白版就按主题换文件——比 CSS 滤镜保真，
                        # 也能做到「只翻文字、保留品牌色」这种混合处理。
                        inner = (f'<img class="logo-light" src="{e(u(en["logo"]))}" alt="" loading="lazy">'
                                 f'<img class="logo-dark" src="{e(u(en["logo_dark"]))}" alt="" loading="lazy">')
                    else:
                        inner = f'<img src="{e(u(en["logo"]))}" alt="" loading="lazy">'
                cls = "cv-row__logo cv-row__logo--flip" if en.get("logo_invert_dark") else "cv-row__logo"
                logo = f'<div class="{cls}" aria-hidden="true">{inner}</div>'
            rows.append(f'<div class="cv-row">{logo}<div class="cv-row__when">{e(en.get("when", ""))}</div>'
                        f'<div class="cv-row__what"><strong>{e(en.get("what", ""))}</strong>{where}{note}</div></div>')
        cls = "cv-block cv-block--logos" if has_logo else "cv-block"
        blocks.append(f'<section class="{cls}"><div class="section__head"><h2>{e(sec["title"])}</h2></div>'
                      f'{"".join(rows)}</section>')

    body = f"""<div class="wrap">
  {page_head("curriculum vitae", "CV")}
  {"".join(blocks) or '<p class="empty">No CV entries yet.</p>'}
</div>"""
    return shell(site, title="CV", active="cv.html", body=body)


def render_notes(site, posts) -> str:
    items = "".join(
        f'<div class="post-item"><div class="post-item__date">{e(p["date"])}</div>'
        f'<div><div class="post-item__title"><a href="{u("notes/" + p["slug"] + ".html")}">{e(p["title"])}</a></div>'
        f'<div class="post-item__excerpt">{e(p["excerpt"])}</div></div></div>'
        for p in posts)
    body = f"""<div class="wrap">
  {page_head("notes", "Notes", "Method, design observations, and things I have not figured out yet.")}
  <div class="post-list">{items or '<p class="empty">No notes yet.</p>'}</div>
</div>"""
    return shell(site, title="Notes", active="notes.html", body=body)


def render_post(site, post) -> str:
    tags = "".join(f'<span class="tag">{e(t)}</span>' for t in post["tags"])
    body = f"""<div class="wrap">
  <header class="page-head">
    <span class="label">{e(post["date"])}</span>
    <h1>{e(post["title"])}</h1>
    <div class="card__foot" style="margin-top:.75rem">{tags}</div>
  </header>
  <article class="prose">{post["html"]}</article>
  <p style="margin-top:3rem"><a href="{u('notes.html')}">← Back to Notes</a></p>
</div>"""
    return shell(site, title=post["title"], active="notes.html", body=body,
                 desc=post["excerpt"], path=f"notes/{post['slug']}.html")


def render_404(site) -> str:
    body = f"""<div class="wrap">
  {page_head("404", "Page not found",
             "That address does not exist — it may have moved, or the link may be wrong.")}
  <div class="pills">{"".join(f'<a class="pill" href="{u(h)}">{e(l)}</a>' for l, h in NAV_ACTIVE)}</div>
</div>"""
    return shell(site, title="Page not found", active="", body=body, path="404.html")


def favicon_svg(site: dict) -> str:
    """姓名首字母 + 强调色的方形图标，直角，跟站点一致。"""
    initials = "".join(w[0] for w in site["name"].split()[:2]).upper() or "?"
    size = 30 if len(initials) > 1 else 38
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
        f'<rect width="64" height="64" fill="{ACCENT}"/>'
        f'<text x="32" y="32" fill="#fff" text-anchor="middle" '
        f'dominant-baseline="central" font-family="Helvetica,Arial,sans-serif" '
        f'font-size="{size}" font-weight="700" letter-spacing="-1">{e(initials)}</text>'
        '</svg>\n'
    )


def render_sitemap(site: dict, pages: list[str], posts: list[dict],
                   projects: list[dict] | None = None) -> str | None:
    site_url = (site.get("url") or "").rstrip("/")
    if not site_url:
        return None
    today = date.today().isoformat()
    locs = []
    for name in pages:
        if name == "404.html":
            continue
        loc = f"{site_url}/{name}"
        if loc.endswith("/index.html"):
            loc = loc[: -len("index.html")]
        locs.append(loc)
    locs += [f"{site_url}/notes/{p['slug']}.html" for p in posts]
    for pr in (projects or []):
        locs.append(f"{site_url}/projects/{pr.get('slug') or slugify(pr['name'])}.html")

    entries = "\n".join(
        f"  <url><loc>{e(l)}</loc><lastmod>{today}</lastmod></url>" for l in locs)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            f"{entries}\n</urlset>\n")


def render_robots(site: dict) -> str:
    site_url = (site.get("url") or "").rstrip("/")
    txt = "User-agent: *\nAllow: /\n"
    if site_url:
        txt += f"\nSitemap: {site_url}/sitemap.xml\n"
    return txt


def render_games(site, plays) -> str:
    body = f"""<div class="wrap">
  {page_head("games", "Play Notes",
             "Not reviews. What I took away from each one, as someone who makes games.")}
  <div class="plays">{"".join(play_entry(g) for g in plays) or '<p class="empty">Nothing here yet.</p>'}</div>
</div>"""
    return shell(site, title="Play Notes", active="games.html", body=body)


# ── 主流程 ────────────────────────────────────────────────────────────────

def main() -> int:
    global BASE

    site_data = load("site.toml")
    if not site_data:
        print("! 找不到 data/site.toml", file=sys.stderr)
        return 1

    site = site_data["site"]
    BASE = (site.get("base_url") or "").rstrip("/")
    news = site_data.get("news", [])
    pubs = load("publications.toml").get("pub", [])
    projects = load("projects.toml").get("project", [])
    cv = load("cv.toml")
    plays = load("games.toml").get("play", [])
    posts = read_posts()

    # 同年内按会议实际月份排；同年同月的保持 publications.toml 里的先后顺序
    pubs.sort(key=lambda p: (p.get("year", 0), p.get("month", 0)), reverse=True)

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    shutil.copytree(ASSETS, OUT / "assets")

    global NAV_ACTIVE
    empty = set()
    if not posts:
        empty.add("notes.html")
    if not plays:
        empty.add("games.html")
    NAV_ACTIVE = [(l, h) for l, h in NAV if h not in empty]

    pages = {
        "index.html": render_index(site, pubs, projects, posts, news),
        "publications.html": render_publications(site, pubs),
        "projects.html": render_projects(site, projects),
        "cv.html": render_cv(site, cv),
        "404.html": render_404(site),
    }
    if posts:
        pages["notes.html"] = render_notes(site, posts)
    if plays:
        pages["games.html"] = render_games(site, plays)
    for name, content in pages.items():
        (OUT / name).write_text(content, encoding="utf-8")

    (OUT / "projects").mkdir(exist_ok=True)
    for pr in projects:
        slug = pr.get("slug") or slugify(pr["name"])
        (OUT / "projects" / f"{slug}.html").write_text(render_project(site, pr), encoding="utf-8")

    (OUT / "notes").mkdir(exist_ok=True)
    for p in posts:
        (OUT / "notes" / f"{p['slug']}.html").write_text(render_post(site, p), encoding="utf-8")

    # 站点级附属文件
    (OUT / "favicon.svg").write_text(favicon_svg(site), encoding="utf-8")
    (OUT / "robots.txt").write_text(render_robots(site), encoding="utf-8")
    sitemap = render_sitemap(site, list(pages), posts, projects)
    if sitemap:
        (OUT / "sitemap.xml").write_text(sitemap, encoding="utf-8")

    # 自定义域名：GitHub Pages 要求发布目录里有 CNAME 文件。
    # 在网页上绑定域名时 GitHub 会自己提交一个，但 build.py 每次都会清空 docs/，
    # 下次构建就把它删了、域名随即失效。所以必须由生成器写出来。
    # 默认域名（*.github.io）不能写，写了反而会让 Pages 认成自定义域名。
    host = urlparse(site.get("url") or "").netloc
    if host and not host.endswith(".github.io"):
        (OUT / "CNAME").write_text(host + "\n", encoding="utf-8")

    total = len(pages) + len(posts) + len(projects)
    print(f"✓ 生成 {total} 个页面 → {OUT}")
    print(f"  论文 {len(pubs)} · 作品 {len(projects)} · 文章 {len(posts)} · 游戏 {len(plays)}")

    # 上线前的自检：缺什么直接说，别等推上去才发现
    warn = []
    if not (site.get("url") or "").strip():
        warn.append("data/site.toml 的 url 没填 → 没有 canonical / og:url / sitemap.xml")
    if not has_asset("assets/css/fonts.css"):
        warn.append("字体未自托管 → 先跑 python tools/fetch_fonts.py")
    if not has_asset("assets/img/og.png"):
        warn.append("缺 og:image → 跑 python tools/make_og.py")
    if not has_asset(site.get("photo", "")):
        warn.append(f"缺头像 → 放一张方图到 {site.get('photo', 'assets/img/profile.jpg')}")
    missing_img = [p["name"] for p in projects if not has_asset(p.get("image", ""))]
    if missing_img:
        warn.append(f"{len(missing_img)} 个作品没有配图 → Projects 页会显示占位块："
                    + "、".join(missing_img[:3]) + ("…" if len(missing_img) > 3 else ""))
    try:
        import markdown  # noqa: F401
    except ImportError:
        warn.append("未装 markdown 包，文章用内置精简解析器渲染（pip install markdown 可获得完整语法）")

    if warn:
        print("\n  上线前还缺：")
        for w in warn:
            print(f"   · {w}")
    return 0


if __name__ == "__main__":
    code = main()
    if code == 0 and "--serve" in sys.argv:
        import http.server
        import socketserver
        import functools
        port = 8000
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(OUT))
        print(f"→ http://localhost:{port}")
        with socketserver.TCPServer(("", port), handler) as httpd:
            httpd.serve_forever()
    sys.exit(code)
