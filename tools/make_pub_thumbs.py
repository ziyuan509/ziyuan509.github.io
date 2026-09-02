#!/usr/bin/env python3
"""
从论文 PDF 里抽取配图，处理成 Publications 页要的 4:3 缩略图。

    python tools/make_pub_thumbs.py            # 生成
    python tools/make_pub_thumbs.py --list     # 只列出候选图，用来挑图

产出 assets/img/pubs/*.jpg（720×540，桌面显示 184×138）。
论文 PDF 放在 papers/ 下，已在 .gitignore 里，不进仓库。

换图：改下面 PICKS 里的 (页码, 图片序号)，先用 --list 查序号。
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

import pypdf.filters as _F
for _n in ("MAX_DECLARED_STREAM_LENGTH", "MAX_ARRAY_BASED_STREAM_OUTPUT_LENGTH",
           "JBIG2_MAX_OUTPUT_LENGTH", "LZW_MAX_OUTPUT_LENGTH",
           "RUN_LENGTH_MAX_OUTPUT_LENGTH", "ZLIB_MAX_OUTPUT_LENGTH",
           "FLATE_MAX_BUFFER_SIZE"):
    setattr(_F, _n, 2_000_000_000)

from pypdf import PdfReader
from PIL import Image

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
PAPERS = ROOT / "papers"
OUT = ROOT / "assets" / "img" / "pubs"

W, H = 720, 540          # 4:3；页面上显示 184×138，这里留了 retina 余量

# slug -> (pdf 文件名, 页码, 图片序号, 说明)
PICKS = {
    "affective-xr":   ("affective-xr.pdf",     1, 0, "Figure 1：affective XR 系统示例"),
    "privacy-rules":  ("privacy-rules.pdf",    3, 0, "原型界面组图"),
    "companion-animal": ("companion-animal.pdf", 4, 0, "系统架构 / 结果图"),
}


def fit_4to3(im: Image.Image) -> Image.Image:
    """居中裁成 4:3。过宽的横幅图（如论文首页的组图）保留中间主体。"""
    im = im.convert("RGB")
    w, h = im.size
    target = 4 / 3
    if w / h > target:
        new_w = int(h * target)
        left = (w - new_w) // 2
        im = im.crop((left, 0, left + new_w, h))
    else:
        new_h = int(w / target)
        top = (h - new_h) // 2
        im = im.crop((0, top, w, top + new_h))
    return im.resize((W, H), Image.LANCZOS)


def candidates(pdf: Path, max_pages: int = 4) -> None:
    reader = PdfReader(str(pdf))
    print(f"\n--- {pdf.name} ({len(reader.pages)} 页) ---")
    for pno, page in enumerate(reader.pages[:max_pages], 1):
        try:
            imgs = page.images
        except Exception as exc:
            print(f"  p{pno}: {type(exc).__name__}")
            continue
        for idx, obj in enumerate(imgs):
            try:
                im = Image.open(io.BytesIO(obj.data))
            except Exception:
                continue
            if min(im.size) < 200:
                continue
            print(f"  p{pno} #{idx:02d}  {im.size[0]}×{im.size[1]}  ratio {im.size[0]/im.size[1]:.2f}")


def main() -> int:
    if not PAPERS.exists():
        print(f"! 找不到 {PAPERS}（论文 PDF 放这里）", file=sys.stderr)
        return 1

    if "--list" in sys.argv:
        for pdf in sorted(PAPERS.glob("*.pdf")):
            candidates(pdf)
        return 0

    OUT.mkdir(parents=True, exist_ok=True)
    for slug, (name, page_no, img_idx, note) in PICKS.items():
        path = PAPERS / name
        if not path.exists():
            print(f"! 跳过 {slug}：找不到 {name}")
            continue
        try:
            reader = PdfReader(str(path))
            src = Image.open(io.BytesIO(reader.pages[page_no - 1].images[img_idx].data))
        except Exception as exc:
            print(f"! {slug}: {type(exc).__name__}: {exc}", file=sys.stderr)
            continue
        dest = OUT / f"{slug}.jpg"
        fit_4to3(src).save(dest, quality=86, optimize=True, progressive=True)
        print(f"✓ {dest.relative_to(ROOT)}  {W}×{H}  "
              f"{dest.stat().st_size/1024:5.1f} KB   ← {name} p{page_no} #{img_idx}  {note}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
