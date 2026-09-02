#!/usr/bin/env python3
"""
处理作品页要用的图片和视频。

    python tools/make_project_images.py

来源在 projects/ 下（近 1 GB，已在 .gitignore 里，不进仓库）：
    projects/image/<项目名>/…   手工挑选的图
    projects/video/…            视频源

产出到 assets/img/projects/ 和 assets/video/：
    <slug>-card.jpg     列表页卡片，16:10 居中裁切（网格要统一，所以裁）
    <slug>.jpg          详情页头图，保持原比例，只限宽
    <slug>-<名>.jpg     详情页正文配图，保持原比例，只限宽
    <slug>-<名>.mp4     由 GIF 转出的视频

为什么正文配图不裁：这些是带标注的技术图，裁切会切掉标注和信息。
只有卡片需要统一比例，所以只裁那一张。

GIF 转 MP4 是因为三个 GIF 加起来 27 MB，直接放网页上手机流量打不开；
转成 H.264 后能小一个数量级，还能自动循环播放。
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "projects" / "image"
OUT = ROOT / "assets" / "img" / "projects"
VOUT = ROOT / "assets" / "video"

CARD_W, CARD_H = 1200, 750     # 16:10，列表页卡片
HERO_W = 1800                  # 详情页头图限宽
FIG_W = 1440                   # 正文配图限宽
VIDEO_W = 960                  # 视频宽度

# slug -> {hero: 相对 projects/image 的路径或 None（None = 保留现有头图）,
#          figs: [(后缀, 路径), …]}
CURATED = {
    "was-here": {
        "hero": "Was Here From Presence to Trace/title.png",
        "figs": [("plan",   "Was Here From Presence to Trace/1 scene.png"),
                 ("frames", "Was Here From Presence to Trace/2 installation image.png")],
    },
    "telepathic-jar": {
        "hero": None,
        "figs": [("circuit", "Telepathic Jar/1 hardware.png"),
                 ("built",   "Telepathic Jar/2 final.png")],
    },
    "dislocation": {
        "hero": "Dislocation Communication/title.png",
        "figs": [("iceberg", "Dislocation Communication/1 UI.png"),
                 ("restore", "Dislocation Communication/3 final.png")],
    },
    "touch-it": {
        "hero": None,
        "figs": [("mapping",  "TOUCH IT!/Frame 2609502.png"),
                 ("software", "TOUCH IT!/Frame 2609503.png")],
    },
    "theta": {
        "hero": "theta/cover.png",
        "figs": [],
    },
}

# slug -> [(后缀, GIF 路径, 说明), …]
VIDEOS = {
    "theta": [
        ("settings", "theta/Settings UI.gif",  "径向设置盘"),
        ("tutorial", "theta/tutorial UI.gif",  "操作指引"),
        ("bird",     "theta/BirdLonger.gif",   "环形谜题"),
    ],
}


def ffmpeg_exe() -> str | None:
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def limit_width(im: Image.Image, w: int) -> Image.Image:
    """只限宽，保持原比例。图本来就窄的不放大。"""
    im = im.convert("RGB")
    if im.width <= w:
        return im
    return im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)


def crop_box(im: Image.Image, tw: int, th: int) -> Image.Image:
    """居中裁成目标比例。"""
    im = im.convert("RGB")
    w, h = im.size
    target = tw / th
    if w / h > target:
        nw = int(h * target)
        im = im.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
    else:
        nh = int(w / target)
        im = im.crop((0, (h - nh) // 2, w, (h - nh) // 2 + nh))
    return im.resize((tw, th), Image.LANCZOS)


def save(im: Image.Image, dest: Path, q: int = 84) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    im.save(dest, quality=q, optimize=True, progressive=True)
    print(f"  {dest.relative_to(ROOT).as_posix():<46} {im.width}×{im.height}  "
          f"{dest.stat().st_size / 1024:6.1f} KB")


def main() -> int:
    if not SRC.exists():
        print(f"! 找不到 {SRC}", file=sys.stderr)
        return 1
    OUT.mkdir(parents=True, exist_ok=True)

    for slug, spec in CURATED.items():
        print(f"\n{slug}")
        hero_src = None
        if spec["hero"]:
            hero_src = SRC / spec["hero"]
            if not hero_src.exists():
                print(f"  ! 缺 {spec['hero']}", file=sys.stderr)
                hero_src = None

        if hero_src:
            im = Image.open(hero_src)
            save(limit_width(im, HERO_W), OUT / f"{slug}.jpg")
            save(crop_box(im, CARD_W, CARD_H), OUT / f"{slug}-card.jpg")
        elif (OUT / f"{slug}.jpg").exists():
            # 沿用现有头图，只补一张卡片图
            save(crop_box(Image.open(OUT / f"{slug}.jpg"), CARD_W, CARD_H),
                 OUT / f"{slug}-card.jpg")

        for name, rel in spec["figs"]:
            p = SRC / rel
            if not p.exists():
                print(f"  ! 缺 {rel}", file=sys.stderr)
                continue
            save(limit_width(Image.open(p), FIG_W), OUT / f"{slug}-{name}.jpg", q=86)

    # ── GIF → MP4 ──────────────────────────────────────────────
    exe = ffmpeg_exe()
    if not exe:
        print("\n! 找不到 ffmpeg，跳过视频转换（pip install imageio-ffmpeg）", file=sys.stderr)
        return 0

    VOUT.mkdir(parents=True, exist_ok=True)
    print("\n视频")
    for slug, items in VIDEOS.items():
        for name, rel, note in items:
            src = SRC / rel
            if not src.exists():
                print(f"  ! 缺 {rel}", file=sys.stderr)
                continue
            dest = VOUT / f"{slug}-{name}.mp4"
            poster = OUT / f"{slug}-{name}-poster.jpg"
            cmd = [exe, "-y", "-loglevel", "error", "-i", str(src),
                   # 宽度定死、高度取偶数（H.264 要求）
                   "-vf", f"scale={VIDEO_W}:-2:flags=lanczos",
                   "-c:v", "libx264", "-profile:v", "main", "-pix_fmt", "yuv420p",
                   "-crf", "26", "-preset", "slow", "-an",
                   "-movflags", "+faststart", str(dest)]
            try:
                subprocess.run(cmd, check=True, capture_output=True)
            except subprocess.CalledProcessError as exc:
                print(f"  ! {dest.name}: {exc.stderr.decode(errors='replace')[:160]}", file=sys.stderr)
                continue
            before = src.stat().st_size / 1048576
            after = dest.stat().st_size / 1048576
            print(f"  {dest.relative_to(ROOT).as_posix():<40} "
                  f"{before:5.1f} MB → {after:4.1f} MB  ({before/after:.0f}× 更小)  {note}")

            # 首帧做 poster，视频没加载出来时先显示它
            g = Image.open(src)
            g.seek(0)
            save(limit_width(g.convert("RGB"), FIG_W), poster, q=80)
    return 0


if __name__ == "__main__":
    sys.exit(main())
