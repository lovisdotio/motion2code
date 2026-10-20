# Verification

Agents animate blind. Every claim about the result needs an image you looked at or a number a script printed.

## The loop of work

1. Build a first pass of every shot (rough is fine).
2. `frame_diff.py` every 0.5 s; open the sheet and the worst pairs; fix structure (wrong shape, wrong place, wrong
   beat) before details.
3. Zoom on each transition at full frame rate (`--every 1/24 --start a --end b`): timing and easing problems only
   show here.
4. Polish: colors, line weights, faces, secondary motion.
5. `check_anim.py --runtime` until clean, then render the proof videos.

## frame_diff.py

```bash
python3 scripts/frame_diff.py source.mp4 index.html -o diff/                      # every 0.5 s
python3 scripts/frame_diff.py source.mp4 index.html -o diff/ --at 0.5 3 6 9 12 14.5
python3 scripts/frame_diff.py source.mp4 index.html -o d2/ --every 1/24 --start 6.8 --end 7.4
```

Writes `pair_t006.000.png` (source left, code right), `sheet.png` (all pairs) and `diff.json` with the 5 worst
times. The score is a mean absolute RGB difference at 192x108: useful to rank moments, not a verdict. A shape
offset by a few pixels scores low but can look wrong; a correct beat 2 frames late can score high. Open the images.

Typical scores for a faithful flat rebuild: under 10 on holds, 10 to 30 during fast motion (the AI frame has
motion blur and noise the vector frame does not), above 40 means a wrong shape, color or beat.

## compare.html

`templates/compare.html` next to `index.html`, source at `source.mp4` (or `compare.html?src=../path/clip.mp4`).
Serve the folder (`python3 -m http.server 8000 --bind 127.0.0.1`) and open it. The code iframe follows the video
clock (`anim.seek(video.currentTime)`), so the two are synced frame by frame. Arrow keys step one frame, space
plays/pauses, "Onion skin" lays the code at 50 % over the video to check alignment.

## check_anim.py

```bash
python3 scripts/check_anim.py index.html              # static: contract, allowlist, no raster, no personal paths
python3 scripts/check_anim.py index.html --runtime    # + browser: console, network, seam, determinism, autoplay
python3 scripts/check_anim.py site.html               # static checks adapted to interactive pages
```

## Proof videos

```bash
python3 scripts/render_anim.py index.html -o anim.mp4                 # exact frames via anim.seek, 24 fps
python3 scripts/side_by_side.py source.mp4 anim.mp4 -o side_by_side.mp4 --html index.html
python3 scripts/render_anim.py index.html --gif poster.gif --gif-range 0 4 --gif-width 480
```

Never screen-record the page in real time to make these: headless browsers drop and duplicate frames. The render
script seeks each frame, so the output is identical run after run.

Vectors render at any size: `render_anim.py --size 3840x2160` (4K) or larger re-renders the same page sharply,
something the source video cannot do. For HTML/CSS layouts that are not a single SVG, keep the stage size and
use a larger device scale in your own capture instead.

## Report

State, with numbers: the frame_diff times checked and the worst ones (and why they remain), the
`check_anim --runtime` line, the page size, and what differs from the source.
