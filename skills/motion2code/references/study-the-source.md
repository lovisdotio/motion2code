# Study the source

You cannot play the video. Everything you know about it comes from images you extract and look at. Spend real time
here: most failed conversions are wrong timing or a missed beat, not bad SVG.

## 1. Extract

```bash
python3 scripts/study_video.py source.mp4 -o study/                 # frame every 0.25 s, cuts, sheet, palette
python3 scripts/study_video.py source.mp4 -o study/ --every 0.125   # fast clips: every 3 frames at 24 fps
python3 scripts/palette.py source.mp4 --at 0 4.2 9.8                # exact fills at specific moments
```

- `study/sheet.png` first (one tile every 0.5 s, row-major), to see the whole story at once.
- Then `study/frames/` in order. AI motion design changes something about every second; at 0.25 s you see each
  beat 3 to 4 times. Use `--every 1/24` style zooms later, around transitions only.
- `study/cuts/` holds the frame before and after every hard change. In "one continuous shot" AI videos a cut is
  usually a morph, an iris or a wipe that happens in 2 to 4 frames: look at those frames one by one.
- `study.json` gives `duration`, `fps`, `width`, `height`, the palette and `source_loop_seam` (mean difference
  between the first and the last frame; under about 6 the source already loops).

## 2. Read the prompt

If a `.txt` prompt sits next to the video, it is the authority for words and for intent (the beats per second,
"the last shape becomes the first shape of the next moment", "loops back to the opening frame"). The video wins
for timing, shapes and colors; the prompt wins for spelling. Video models misspell and invent words: write
the prompt's words, exactly, and drop any word the prompt does not contain.

## 3. Duration and stage

- Real duration from ffprobe. Generators return 10.10 or 15.10 s for a 10 or 15 s request: the animation lasts
  10 or 15 s, and `compare.html` wraps the video at the animation's duration.
- Stage = source resolution: `viewBox="0 0 1920 1080"` (16:9) or `0 0 1080 1920` (9:16). Keep the coordinate
  system in source pixels so you can measure positions directly on the frames (a 960 px wide frame is half scale).

## 4. Palette

Flat motion design uses 4 to 8 solid fills. `palette.py` bins and merges pixels and prints the cluster means as
hex with their share; anti-aliased edges fall below the share cut. Prefer sampling at a time where each color
covers a large area. AI video drifts colors slightly over time (compression, model noise): pick one value per
role (background, ink, accent) and keep it constant unless the source clearly changes it.

## 5. Shot list

Write it before coding, one line per beat, in source time:

```text
0.00-1.20  OPEN   green cup centered (cx 960, rim y 470, w 560), cream foam heart, lilac bg
1.20-2.30  SIP    cherry blob slides in from right (back.out), leans, squash on contact at 1.9
2.30-3.50  TURN   blob face fills green from the chin up (clip rect rising), eyes blink at 3.1
...
13.80-15.0 RETURN everything snaps back to OPEN, hard stop at 14.6, hold
```

Per beat, note:
- what enters, what leaves, what transforms into what (AI loops chain shapes: the last shape of one beat is the
  first shape of the next, so most transitions are morphs, scales and wipes, not cuts);
- positions and sizes measured on the frames (centers, radii, baselines);
- the feel: snap, ease out, overshoot, elastic settle, linear drift (see `motion-vocabulary.md`);
- secondary motion: blinks, wobbles, drops, sparkles, sound rings.

## 6. What to keep, what to simplify

Keep: silhouettes, timing, colors, faces (eyes, lids, cheeks carry the character), squash and stretch, the order
of beats, every readable word. Simplify only noise the model added (jittering specks, smudged textures, warping
details that change every frame), and say so in the report.
