# Interfaces and real sites

Video models produce convincing "screen recordings" of websites and apps. There are two deliverables:

1. **The replay** (`index.html`): a faithful, seekable, looping rebuild of the recording, with the same contract as
   any other clip, the fake cursor or touch point included.
2. **The real site** (`site.html`, optional): the same design made usable. No fake cursor: the user scrolls,
   clicks, drags. Build it after the replay, from the replay's drawings.

## The replay

- Rebuild the interface as real layout: a grid, header, menus, cards, buttons, in HTML/CSS + inline SVG, or as one
  SVG when the recording is mostly illustration. Flat fills only, no images.
- Running text stays as flat bars (rounded rects of the measured line widths), as in the recording. The only real
  words are the ones the prompt lists, spelled exactly. Gibberish menu labels invented by the model become bars or
  are removed.
- The cursor is a small shape with its own keyframes (position, press scale). Clicks: a 2 to 3 frame press
  (scale 0.9) at the time the frames show the state change starting.
- Scrolling in the recording is a translate of the page group, keyed from the frames.
- Vertical recordings (1080x1920): stage `viewBox="0 0 1080 1920"`; `side_by_side.py` switches to the portrait
  layout automatically.
- The recording loops like any clip: the interface is back on its opening view at the end.

## The real site (site.html)

Same look (drawings, colors, fonts, layout), real behavior. Start from `templates/site.html`.

| In the recording | In site.html |
|---|---|
| Page scrolls, sections slide in | real scroll; `ScrollTrigger` reveals (`start: 'top 85%'`) |
| A scene changes while scrolling (day to night, map unfolds) | pinned section with a scrubbed timeline (`pin: true, scrub: 0.6`) |
| Cursor clicks a menu | `<button aria-expanded aria-controls>` opening a panel, Escape closes it |
| Clicks play | a toggle button with `aria-pressed`, the icon/label really changes, ambient motion starts/stops |
| Drags a slider | `role="slider"` with pointer capture (mouse and touch) and arrow keys, `aria-valuenow` |
| Tabs change | `role="tablist"`, arrow keys move between tabs |
| Card flips or grows | a `<button>` toggling state, GSAP flip/scale |
| Add to cart | counter that increments with a pop, `aria-live="polite"` |
| Pulses, rings, bobbing | ambient GSAP loops (`repeat: -1, yoyo: true`), off under reduced motion |

Rules:
- Links and buttons are real `<a>` and `<button>` with `aria-label` where the label is an icon.
- Everything works with the keyboard (Tab, Enter, Space, arrows, Escape) and has a visible focus style.
- Responsive from 1920 px to 375 px, no horizontal scroll. Phone apps stay vertical: centered on desktop, full
  screen on mobile.
- `prefers-reduced-motion: reduce`: no ambient loops, instant state changes, scrub without smoothing.
- Zero console errors. Only GSAP (+ ScrollTrigger, ScrollToPlugin) from cdnjs and Google Fonts.
- Readable words stay the prompt's words; short plain labels may be added when a control would otherwise be
  unclear, in the language of the prompt.
- Set `document.documentElement.dataset.ready = '1'` after fonts load and `ScrollTrigger.refresh()`.

## Checking a site

With Playwright, at 1920x1080 and 375x812: scroll the whole page (scroll to each ScrollTrigger `start` and
inside the pinned ranges, not to `offsetTop`, which pinning changes), click every control, drag every slider,
press Escape and the arrow keys, screenshot each state and open the screenshots. Assert no console errors and no
horizontal overflow (`document.documentElement.scrollWidth <= innerWidth`). `check_anim.py site.html` runs the
static checks.

For a demo video of the site, record a scripted Playwright session (real scrolls and clicks) with a small
visible cursor drawn only during the recording, then convert to H.264 with faststart.
