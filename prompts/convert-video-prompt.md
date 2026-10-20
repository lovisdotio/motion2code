# Prompt: rebuild a video as SVG + GSAP code

Use the **motion2code** skill (read its `SKILL.md` first and follow its workflow) to rebuild the video below as one
self-contained `index.html`: inline SVG, one GSAP timeline, `window.anim` contract, seamless loop.

Fill these in before sending (leave a line blank to let the agent measure it):

- **Source video:** `<path>`
- **Generation prompt (exact words):** `<path to the .txt, or paste it, or blank>`
- **Output folder:** `<folder>` (files: `index.html`, `compare.html`, optionally `site.html`)
- **Must keep:** `<the beats, characters or words you care about most, or blank>`
- **Interface recording?** `<yes: also build site.html with real scroll and clicks / no>`
- **Proof videos?** `<yes: anim.mp4 and side_by_side.mp4 / no>`

The video is the spec. You derive everything from its frames.

## Done means

- `study_video.py` was run and the sheet and frames were looked at before any code.
- `index.html` follows the page contract (`seek`, `?t=`, `?external=1`, `data-ready`, autoplay and loop).
- Only the source video was used; nothing regenerated, embedded or traced.
- Every readable word is the prompt's word, spelled exactly.
- `frame_diff.py` was run every 0.5 s and frame by frame on each transition; the worst times were fixed or are
  explained.
- `check_anim.py index.html --runtime` prints `[ok]` (seam, determinism, console, network).
- The report lists what differs from the source, with numbers.
