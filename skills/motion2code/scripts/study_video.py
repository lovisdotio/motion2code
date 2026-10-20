#!/usr/bin/env python3
"""Turn a source video into things an agent can look at: frames, cuts, a contact sheet, a palette, a loop score.

  python3 study_video.py source.mp4 -o study/
  python3 study_video.py source.mp4 -o study/ --every 0.125 --cut 0.25

Writes into the output folder:
  frames/t0000.00.png ...   one frame every --every seconds (960 px wide), named by time
  cuts/                     the frame just before and just after every detected cut / hard change
  sheet.png                 contact sheet, one tile every --sheet-every seconds, row-major, left to right
  study.json                size, fps, duration, cut times, palette, source loop score

Then open the sheet and the frames with your image viewer / Read tool. Never animate from memory of the video.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _m2c import mean_abs_diff, need, probe, save_frame_png, video_frame_rgb  # noqa: E402
from palette import palette_from_rgb  # noqa: E402


def extract_frames(video: Path, out: Path, every: float, width: int, info: dict) -> list[float]:
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("t*.png"):
        old.unlink()
    tmp = out / "_f%05d.png"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-vf",
                    f"fps=1/{every}:round=down,scale={width}:-2", str(tmp)], check=True)
    times = []
    for i, f in enumerate(sorted(out.glob("_f*.png"))):
        t = i * every
        if t > info["duration"]:
            f.unlink()
            continue
        f.rename(out / f"t{t:07.2f}.png")
        times.append(round(t, 3))
    # always include the very last frame (loop seam)
    save_frame_png(video, info["duration"], out / f"t{info['duration']:07.2f}_last.png", width)
    return times


def detect_cuts(video: Path, threshold: float) -> list[float]:
    r = subprocess.run(["ffmpeg", "-v", "info", "-i", str(video), "-vf",
                        f"select='gt(scene,{threshold})',showinfo", "-f", "null", "-"],
                       capture_output=True, text=True)
    return [round(float(m), 3) for m in re.findall(r"pts_time:([\d.]+)", r.stderr)]


def contact_sheet(video: Path, out: Path, every: float, info: dict, cols: int = 6, tile_w: int = 320):
    n = max(1, int(info["duration"] / every))
    rows = math.ceil(n / cols)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-vf",
                    f"fps=1/{every}:round=down,scale={tile_w}:-2,tile={cols}x{rows}:padding=4:margin=4:color=0x111111",
                    "-frames:v", "1", str(out)], check=True)
    return {"cols": cols, "rows": rows, "every": every}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("-o", "--out", default="study")
    ap.add_argument("--every", type=float, default=0.25, help="seconds between saved frames (default 0.25)")
    ap.add_argument("--width", type=int, default=960)
    ap.add_argument("--cut", type=float, default=0.3, help="scene-change threshold 0..1 (lower finds more)")
    ap.add_argument("--sheet-every", type=float, default=0.5)
    a = ap.parse_args()
    need("ffmpeg")
    video, out = Path(a.video), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    info = probe(video)
    print(f"{video.name}: {info['width']}x{info['height']} {info['fps']} fps {info['duration']} s")

    times = extract_frames(video, out / "frames", a.every, a.width, info)
    cuts = detect_cuts(video, a.cut)
    cdir = out / "cuts"
    cdir.mkdir(exist_ok=True)
    for c in cuts:
        save_frame_png(video, max(0, c - 1 / info["fps"]), cdir / f"cut{c:07.2f}_before.png", a.width)
        save_frame_png(video, c, cdir / f"cut{c:07.2f}_after.png", a.width)
    sheet = contact_sheet(video, out / "sheet.png", a.sheet_every, info)

    pal = palette_from_rgb([video_frame_rgb(video, info["duration"] * (i + 0.5) / 12, 320, 180) for i in range(12)])
    first, last = video_frame_rgb(video, 0), video_frame_rgb(video, info["duration"])
    seam = round(mean_abs_diff(first, last), 2)

    study = {"video": video.name, **info, "frames_every": a.every, "frame_count_saved": len(times),
             "cuts": cuts, "sheet": sheet, "palette": pal, "source_loop_seam": seam,
             "source_loops": seam < 6.0}
    (out / "study.json").write_text(json.dumps(study, indent=1))
    print(f"frames: {len(times)} in {out / 'frames'}  (every {a.every} s, plus the last frame)")
    print(f"cuts:   {cuts or 'none detected'}")
    print(f"sheet:  {out / 'sheet.png'}  ({sheet['cols']} x {sheet['rows']} tiles, one every {a.sheet_every} s)")
    print("palette: " + "  ".join(f"{c['hex']} {c['share'] * 100:.0f}%" for c in pal))
    verdict = "source already loops" if study["source_loops"] else "source does NOT loop: the code must add the return"
    print(f"source first/last frame diff: {seam}  -> {verdict}")


if __name__ == "__main__":
    main()
