#!/usr/bin/env python3
"""Sample the exact flat colors of a video (or image).

Flat motion design uses a handful of solid fills. This script decodes frames with ffmpeg, bins pixels, merges near
bins and prints the real mean color of each cluster as hex, with its share of the frame. Anti-aliased edge pixels
fall under --min-share and are dropped.

  python3 palette.py source.mp4                     # whole video, 12 evenly spaced frames
  python3 palette.py source.mp4 --at 0 2.5 7        # only these times
  python3 palette.py frame.png --json               # an image, JSON output
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _m2c import image_rgb, probe, video_frame_rgb  # noqa: E402

W, H = 320, 180


def palette_from_rgb(chunks: list[bytes], merge: float = 26.0, min_share: float = 0.004, top: int = 12) -> list[dict]:
    bins: dict[tuple, list] = {}
    total = 0
    for data in chunks:
        for i in range(0, len(data) - 2, 3):
            r, g, b = data[i], data[i + 1], data[i + 2]
            k = (r >> 3, g >> 3, b >> 3)
            e = bins.get(k)
            if e is None:
                bins[k] = [1, r, g, b]
            else:
                e[0] += 1; e[1] += r; e[2] += g; e[3] += b
            total += 1
    if not total:
        return []
    groups: list[list] = []  # [count, sr, sg, sb]
    for c, sr, sg, sb in sorted(bins.values(), key=lambda e: -e[0]):
        mr, mg, mb = sr / c, sg / c, sb / c
        for gr in groups:
            gr_r, gr_g, gr_b = gr[1] / gr[0], gr[2] / gr[0], gr[3] / gr[0]
            if ((mr - gr_r) ** 2 + (mg - gr_g) ** 2 + (mb - gr_b) ** 2) ** 0.5 < merge:
                gr[0] += c; gr[1] += sr; gr[2] += sg; gr[3] += sb
                break
        else:
            groups.append([c, sr, sg, sb])
    out = []
    for c, sr, sg, sb in sorted(groups, key=lambda g: -g[0]):
        share = c / total
        if share < min_share:
            continue
        out.append({"hex": "#{:02X}{:02X}{:02X}".format(round(sr / c), round(sg / c), round(sb / c)),
                    "share": round(share, 4)})
    return out[:top]


def sample(path: str, times: list[float] | None = None, n: int = 12) -> list[bytes]:
    p = Path(path)
    if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".bmp"}:
        return [image_rgb(p, W, H)]
    info = probe(p)
    if not times:
        times = [info["duration"] * (i + 0.5) / n for i in range(n)]
    return [video_frame_rgb(p, t, W, H) for t in times]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path", help="video or image")
    ap.add_argument("--at", type=float, nargs="*", help="times in seconds (video only)")
    ap.add_argument("--frames", type=int, default=12, help="evenly spaced frames when --at is not given")
    ap.add_argument("--merge", type=float, default=26.0, help="RGB distance under which bins merge")
    ap.add_argument("--min-share", type=float, default=0.004)
    ap.add_argument("--top", type=int, default=12)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    pal = palette_from_rgb(sample(a.path, a.at, a.frames), a.merge, a.min_share, a.top)
    if a.json:
        print(json.dumps(pal, indent=1))
        return
    for c in pal:
        print(f"{c['hex']}  {c['share'] * 100:5.1f} %")


if __name__ == "__main__":
    main()
