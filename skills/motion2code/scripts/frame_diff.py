#!/usr/bin/env python3
"""Compare the coded animation with the source video, frame against frame, side by side.

  python3 frame_diff.py source.mp4 index.html -o diff/                     # every 0.5 s
  python3 frame_diff.py source.mp4 index.html -o diff/ --at 0.5 3 6 9 12 14.5
  python3 frame_diff.py source.mp4 index.html -o diff/ --every 1/24 --start 6.8 --end 7.4   # one transition

For every time t it writes diff/pair_t006.000.png (source left | code right, 960 px each), prints a mean difference
(0 = identical, 255 = opposite) and writes diff/sheet.png with all pairs stacked. The number is a pointer, not a
verdict: flat colors in the wrong place score high, a 3 px offset scores low. Look at every pair image, then fix the
worst times first. Times are in the animation clock; use --offset if the code is shifted against the source.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _m2c import (image_rgb, launch, mean_abs_diff, need, open_anim, parse_size, playwright, probe,  # noqa: E402
                  save_frame_png, seek_shot, serve)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source")
    ap.add_argument("html")
    ap.add_argument("-o", "--out", default="diff")
    ap.add_argument("--at", type=float, nargs="*")
    ap.add_argument("--every", default="0.5", help="step in seconds, fractions allowed (1/24)")
    ap.add_argument("--start", type=float, default=0.0)
    ap.add_argument("--end", type=float)
    ap.add_argument("--offset", type=float, default=0.0, help="source time = code time + offset")
    ap.add_argument("--size", help="viewport WxH (default from the svg viewBox)")
    ap.add_argument("--root", help="folder to serve (default: the page's folder)")
    ap.add_argument("--pair-width", type=int, default=960)
    a = ap.parse_args()
    need("ffmpeg")
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("pair_*.png"):
        old.unlink()
    html = Path(a.html).resolve()
    root = Path(a.root).resolve() if a.root else html.parent
    size = parse_size(a.size, html)
    info = probe(a.source)
    pw = a.pair_width
    ph = round(pw * size[1] / size[0] / 2) * 2

    httpd, base = serve(root)
    rows = []
    try:
        with playwright()() as p:
            browser = launch(p)
            page, dur = open_anim(browser, html, base, root, size)
            end = a.end if a.end is not None else dur
            if a.at:
                times = a.at
            else:
                step = float(Fraction(a.every))
                n = int((end - a.start) / step + 1e-6) + 1
                times = [round(a.start + i * step, 4) for i in range(n)]
            for t in times:
                tag = f"t{t:07.3f}"
                cpath, spath = out / f"_code_{tag}.png", out / f"_src_{tag}.png"
                seek_shot(page, t, cpath)
                save_frame_png(a.source, min(t + a.offset, info["duration"]), spath)
                d = mean_abs_diff(image_rgb(spath, 192, 108), image_rgb(cpath, 192, 108))
                pair = out / f"pair_{tag}.png"
                subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(spath), "-i", str(cpath), "-filter_complex",
                                f"[0:v]scale={pw}:{ph},setsar=1[a];[1:v]scale={pw}:{ph},setsar=1[b];"
                                f"[a]pad={pw + 8}:{ph}:0:0:color=0x111111[a2];[a2][b]hstack", str(pair)], check=True)
                cpath.unlink(); spath.unlink()
                rows.append({"t": t, "diff": round(d, 2), "pair": pair.name})
                print(f"t={t:7.3f}  diff {d:6.2f}  {'#' * min(40, int(d / 3))}")
            browser.close()
    finally:
        httpd.shutdown()
    if len(rows) > 1:
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-pattern_type", "glob", "-i", str(out / "pair_*.png"),
                        "-vf", f"scale=800:-2,tile=2x{(len(rows) + 1) // 2}:padding=6:color=0x000000", "-frames:v", "1",
                        str(out / "sheet.png")], check=True)
    worst = sorted(rows, key=lambda r: -r["diff"])[:5]
    (out / "diff.json").write_text(json.dumps({"rows": rows, "worst": worst}, indent=1))
    print("worst: " + ", ".join(f"{r['t']} s ({r['diff']})" for r in worst))
    print(f"pairs: {out}/pair_*.png   sheet: {out / 'sheet.png'}")


if __name__ == "__main__":
    main()
