#!/usr/bin/env python3
"""Build the side-by-side proof video: AI source on the left, the coded animation on the right.

  python3 side_by_side.py source.mp4 anim.mp4 -o side_by_side.mp4 --html index.html
  python3 side_by_side.py source.mp4 anim.mp4 -o sbs.mp4 --left "AI video" --right "Code" --panel-width 640

Landscape sources give a 1940x620 video (two 960x540 panels under an 80 px label band); portrait sources give
1140x1020 (two 540x960 panels). The output lasts as long as the coded animation, so a 15.10 s source is trimmed to
the animation's 15.00 s. With --html, the right label shows the page size ("Code · SVG + GSAP · 72 KB").
Labels are drawn with Playwright when it is installed (ffmpeg builds often lack drawtext); without it the band is
left empty.
"""
from __future__ import annotations

import argparse
import html as htmllib
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _m2c import human_kb, launch, need, probe  # noqa: E402

BG = "#0b0b0e"


def label_png(path: Path, w: int, band: int, pw: int, gap: int, left: str, right: str, font: int) -> bool:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright not installed: labels skipped")
        return False
    doc = f"""<html><body style="margin:0;width:{w}px;height:{band}px;background:{BG};
      font:700 {font}px/1 'Helvetica Neue',Arial,sans-serif;position:relative">
      <div style="position:absolute;left:0;width:{pw}px;top:0;height:{band}px;display:flex;align-items:center;
        justify-content:center;color:#fff">{htmllib.escape(left)}</div>
      <div style="position:absolute;left:{pw + gap}px;width:{pw}px;top:0;height:{band}px;display:flex;align-items:center;
        justify-content:center;color:#e8ff5a">{htmllib.escape(right)}</div></body></html>"""
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={"width": w, "height": band})
        pg.set_content(doc)
        pg.screenshot(path=str(path))
        b.close()
    return True


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source", help="the AI-generated source video")
    ap.add_argument("code", help="the rendered animation (render_anim.py output)")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--html", help="index.html, to print its size in the right label")
    ap.add_argument("--left", default="AI video")
    ap.add_argument("--right", default="Code · SVG + GSAP")
    ap.add_argument("--panel-width", type=int, help="panel width (default 960 landscape, 540 portrait)")
    ap.add_argument("--fps", type=float, default=24)
    ap.add_argument("--crf", type=int, default=17)
    ap.add_argument("--no-labels", action="store_true")
    a = ap.parse_args()
    need("ffmpeg")
    src, code = probe(a.source), probe(a.code)
    portrait = src["height"] > src["width"]
    pw = a.panel_width or (540 if portrait else 960)
    ph = round(pw * src["height"] / src["width"] / 2) * 2
    gap = 20 if not portrait else 40
    band = 0 if a.no_labels else (60 if portrait else 80)
    font = 22 if portrait else 28
    W, H = 2 * pw + gap, band + ph
    dur = code["duration"]
    right = a.right + (f" · {human_kb(a.html)}" if a.html else "")

    inputs = ["-i", a.source, "-i", a.code]
    fc = (f"color=c={BG}:s={W}x{H}:r={a.fps}:d={dur}[bg];"
          f"[0:v]fps={a.fps},scale={pw}:{ph}:flags=lanczos,setsar=1,setpts=PTS-STARTPTS[l];"
          f"[1:v]fps={a.fps},scale={pw}:{ph}:flags=lanczos,setsar=1,setpts=PTS-STARTPTS[r];"
          f"[bg][l]overlay=0:{band}:shortest=1[x];[x][r]overlay={pw + gap}:{band}:shortest=1[v0]")
    last = "v0"
    with tempfile.TemporaryDirectory() as tmp:
        lab = Path(tmp) / "labels.png"
        if band and label_png(lab, W, band, pw, gap, a.left, right, font):
            inputs += ["-loop", "1", "-i", str(lab)]
            fc += ";[v0][2:v]overlay=0:0:shortest=1[v1]"
            last = "v1"
        subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", fc, "-map", f"[{last}]",
                        "-t", f"{dur}", "-c:v", "libx264", "-crf", str(a.crf), "-pix_fmt", "yuv420p",
                        "-movflags", "+faststart", a.out], check=True)
    print(f"{W}x{H}, {dur:.2f} s -> {a.out}")


if __name__ == "__main__":
    main()
