#!/usr/bin/env python3
"""Render a coded animation frame by frame (window.anim.seek) to an mp4, a GIF poster or PNG frames.

Real-time screen recording drops and doubles frames. This script instead seeks the GSAP timeline to every frame
time, screenshots it and pipes the PNGs to ffmpeg, so the output is exact and repeatable.

  python3 render_anim.py index.html -o anim.mp4                        # full duration, 24 fps, stage size
  python3 render_anim.py index.html -o anim.mp4 --fps 30 --width 960   # downscaled output
  python3 render_anim.py index.html --gif poster.gif --gif-range 0 4   # light GIF for a README
  python3 render_anim.py index.html --png 0 7.5 14.9 --frames-dir shots/

Needs Playwright (`uv run --with playwright python render_anim.py ...`) and ffmpeg. The page is served from its
own folder (--root to serve a parent, e.g. when it loads ../source.mp4) and opened with ?external=1.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _m2c import die, launch, need, open_anim, parse_size, playwright, seek_shot, serve  # noqa: E402


def encode(frames_png, fps: float, out: Path, width: int | None, crf: int):
    vf = ["-vf", f"scale={width}:-2:flags=lanczos"] if width else []
    proc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "image2pipe", "-framerate", str(fps), "-i", "-",
                             *vf, "-c:v", "libx264", "-preset", "medium", "-crf", str(crf), "-pix_fmt", "yuv420p",
                             "-movflags", "+faststart", str(out)], stdin=subprocess.PIPE)
    n = 0
    for png in frames_png:
        proc.stdin.write(png)
        n += 1
    proc.stdin.close()
    if proc.wait() != 0:
        die("ffmpeg encode failed")
    return n


def make_gif(mp4: Path, out: Path, start: float, end: float, width: int, fps: float, colors: int):
    pal = f"fps={fps},scale={width}:-2:flags=lanczos,split[a][b];[a]palettegen=max_colors={colors}:stats_mode=diff[p];" \
          f"[b][p]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(start), "-t", str(end - start), "-i", str(mp4),
                    "-filter_complex", pal, "-loop", "0", str(out)], check=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("html", help="the animation page (index.html)")
    ap.add_argument("-o", "--out", help="output mp4")
    ap.add_argument("--fps", type=float, default=24)
    ap.add_argument("--duration", type=float, help="seconds to render (default: window.anim.duration)")
    ap.add_argument("--start", type=float, default=0.0)
    ap.add_argument("--size", help="viewport WxH (default: the first <svg viewBox>, else 1920x1080)")
    ap.add_argument("--width", type=int, help="scale the output video to this width")
    ap.add_argument("--crf", type=int, default=16)
    ap.add_argument("--root", help="folder to serve (default: the page's folder)")
    ap.add_argument("--frames-dir", help="also keep every PNG frame here")
    ap.add_argument("--png", type=float, nargs="*", help="only screenshot these times (into --frames-dir)")
    ap.add_argument("--gif", help="also write a GIF poster")
    ap.add_argument("--gif-range", type=float, nargs=2, default=[0, 4], metavar=("START", "END"))
    ap.add_argument("--gif-width", type=int, default=480)
    ap.add_argument("--gif-fps", type=float, default=12)
    ap.add_argument("--gif-colors", type=int, default=96)
    a = ap.parse_args()
    if not (a.out or a.gif or a.png is not None):
        die("give -o out.mp4, --gif poster.gif or --png times")
    need("ffmpeg")
    html = Path(a.html).resolve()
    root = Path(a.root).resolve() if a.root else html.parent
    size = parse_size(a.size, html)
    fdir = Path(a.frames_dir) if a.frames_dir else None
    if fdir:
        fdir.mkdir(parents=True, exist_ok=True)

    httpd, base = serve(root)
    try:
        with playwright()() as p:
            browser = launch(p)
            errors: list = []
            page, dur = open_anim(browser, html, base, root, size, errors=errors)
            if not dur:
                die("window.anim.duration is missing: the page must expose window.anim = {duration, seek, play, pause}")
            if a.png is not None:
                if not fdir:
                    fdir = Path(".");
                for t in a.png:
                    seek_shot(page, t, fdir / f"code_t{t:07.3f}.png")
                print(f"{len(a.png)} PNG frames -> {fdir}")
                if not (a.out or a.gif):
                    return
            length = a.duration or (dur - a.start)
            n = int(round(length * a.fps))

            def frames():
                for i in range(n):
                    t = a.start + i / a.fps
                    png = seek_shot(page, t)
                    if fdir:
                        (fdir / f"f{i:05d}.png").write_bytes(png)
                    if i % max(1, n // 10) == 0:
                        print(f"  frame {i}/{n}  t={t:.3f}", flush=True)
                    yield png

            out = Path(a.out) if a.out else Path(tempfile.mkdtemp()) / "anim.mp4"
            count = encode(frames(), a.fps, out, a.width, a.crf)
            browser.close()
            if errors:
                print("console errors:\n  " + "\n  ".join(errors[:10]))
            if a.out:
                print(f"{count} frames ({count / a.fps:.2f} s @ {a.fps} fps, {size[0]}x{size[1]}) -> {out}")
            if a.gif:
                make_gif(out, Path(a.gif), a.gif_range[0], a.gif_range[1], a.gif_width, a.gif_fps, a.gif_colors)
                print(f"GIF {a.gif_range[0]}-{a.gif_range[1]} s @ {a.gif_width}px -> {a.gif}")
    finally:
        httpd.shutdown()


if __name__ == "__main__":
    main()
