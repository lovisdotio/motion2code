---
applyTo: "**/index.html,**/compare.html,**/site.html"
---

Copy this file into your repository's `.github/instructions/`. For agent mode, also install the skill with
`gh skill install lovisdotio/motion2code motion2code`.

- Rebuild the source video as one inline SVG animated by a single GSAP 3 timeline; expose
  `window.anim = { tl, duration, seek(t), play(from), pause() }` with `seek` a pure function of t.
- Support `?t=` (freeze), `?external=1` (no autoplay) and set `<html data-ready="1">` when ready.
- Use only the given source video (no regeneration, no `<img>`/`<video>`/raster in the page), the prompt's exact
  words, flat sampled colors.
- The last moment returns to the exact opening frame. Check with `scripts/check_anim.py --runtime` and compare
  with `scripts/frame_diff.py`.
