#!/usr/bin/env python3
"""
从 projects/ 下的作品集 PDF 里抽取主图，处理成 Projects 页需要的 2:1 横图。

    python tools/make_project_images.py

产出 assets/img/projects/*.jpg（1600×800）。
PDF 本身有近 1 GB，已在 .gitignore 里，不进仓库；只有处理后的图片进仓库。

想换某个项目的主图：改下面 PICKS 里的 (页码, 图片序号)，重跑。
序号可以用 scratchpad 里的盘点脚本查，或者把 DEBUG 设成 True 打印全部候选。
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

# pypdf 6 默认有防解压炸弹的上限，本地可信文件可以放宽
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
PDFS = ROOT / "projects"
OUT = ROOT / "assets" / "img" / "projects"

W, H = 1600, 800          # Projects 页大图是 2:1，桌面显示 944×472

# slug -> (pdf, 页码, 图片序号, 顶部裁掉的比例, 说明)
PICKS = {
    "was-here":       ("01.pdf", 3,  0, 0.00, "走廊砖墙上的四格投影"),
    "telepathic-jar": ("02.pdf", 1,  0, 0.00, "两个亮着不同天气色的瓶子"),
    "dislocation":    ("03.pdf", 4, 19, 0.21, "游戏场景（裁掉顶部 UE 调试文字）"),
    "touch-it":       ("04.pdf", 1, 12, 0.00, "手持手机与外围触控件"),
}


def fit_2to1(im: Image.Image, trim_top: float) -> Image.Image:
    """裁成 2:1。够宽的直接居中裁；竖图放不下就在纯黑画布上居中留边。"""
    im = im.convert("RGB")
    if trim_top:
        im = im.crop((0, int(im.height * trim_top), im.width, im.height))

    w, h = im.size
    if w / h >= 2.0:
        # 横图：按高度定宽，水平居中裁
        new_w = h * 2
        left = (w - new_w) // 2
        im = im.crop((left, 0, left + new_w, h))
        return im.resize((W, H), Image.LANCZOS)

    # 竖图或近方图：等比缩到画布高度，放在黑底上居中
    scale = H / h
    im = im.resize((max(1, int(w * scale)), H), Image.LANCZOS)
    canvas = Image.new("RGB", (W, H), (0, 0, 0))
    canvas.paste(im, ((W - im.width) // 2, 0))
    return canvas


def main() -> int:
    if not PDFS.exists():
        print(f"! 找不到 {PDFS}", file=sys.stderr)
        return 1
    OUT.mkdir(parents=True, exist_ok=True)

    for slug, (pdf_name, page_no, img_idx, trim, note) in PICKS.items():
        path = PDFS / pdf_name
        if not path.exists():
            print(f"! 跳过 {slug}：找不到 {pdf_name}")
            continue
        try:
            reader = PdfReader(str(path))
            images = reader.pages[page_no - 1].images
            src = Image.open(io.BytesIO(images[img_idx].data))
        except Exception as exc:
            print(f"! {slug}: {type(exc).__name__}: {exc}", file=sys.stderr)
            continue

        dest = OUT / f"{slug}.jpg"
        fit_2to1(src, trim).save(dest, quality=84, optimize=True, progressive=True)
        print(f"✓ {dest.relative_to(ROOT)}  {W}×{H}  "
              f"{dest.stat().st_size / 1024:5.1f} KB   ← {pdf_name} p{page_no} #{img_idx}  {note}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
