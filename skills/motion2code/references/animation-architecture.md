# Animation architecture

One HTML file, one inline SVG, one GSAP timeline. Everything visible at time t is a function of t only.

## Stage

```html
<svg id="stage" viewBox="0 0 1920 1080" preserveAspectRatio="xMidYMid meet">
  <defs><clipPath id="frame"><rect width="1920" height="1080"/></clipPath></defs>
  <g clip-path="url(#frame)"> ...layers back to front... </g>
</svg>
```

- `html, body { margin:0; height:100%; overflow:hidden; background:<bg color> }`, the SVG absolutely fills the
  window. The background color matches the stage so letterboxing is invisible.
- Layers as named groups in paint order: `#bg`, `#world`, `#character`, `#fx`, `#type`. Toggle whole layers with
  `display` rather than opacity 0 (cheaper, and screenshots stay exact).
- Draw each object around its own origin (`translate(0 0)` = its center or its contact point: feet, cup base,
  hand). Then position, scale and rotate the group: squash and stretch around the contact point stay correct
  and the same drawing can be reused or retimed.

## The clock: two patterns, one timeline

**Tweens** for classic shot-by-shot motion (most clips):

```js
const tl = gsap.timeline({ paused: true, repeat: -1, defaults: { ease: 'power2.inOut' } });
tl.to('#blob', { scaleX: 1.2, scaleY: 0.8, duration: 0.3, ease: 'power2.in' }, 1.10)   // absolute times
  .to('#blob', { y: 380, duration: 0.35, ease: 'power3.out' }, 1.40)
  .set({}, {}, DUR);                                                                    // exact duration
```

Use absolute positions (third argument in seconds) taken from the shot list, never relative `'+=0.2'` chains:
retiming one beat must not shift every later beat.

**draw(t)** for procedural parts: particles, physics, path morphs, anything easier to compute than to tween.
The shipped examples drive everything this way, with a GSAP tween as the clock:

```js
const clock = { t: 0 };
const tl = gsap.timeline({ repeat: -1, paused: true });
tl.fromTo(clock, { t: 0 }, { t: DUR, duration: DUR, ease: 'none', onUpdate: () => render(clock.t) });
window.anim = {
  tl, duration: DUR,
  seek(t) { t = clamp(t, 0, DUR); tl.pause(); tl.time(t, true); render(t); },
  play(from = 0) { tl.restart(); tl.time(from); tl.play(); },
  pause() { tl.pause(); }
};
```

`render(t)` first resets every element to its opening state, then applies each shot active at t. Because it
starts from scratch every frame, seeking backwards, jumping, and rendering frame 200 before frame 3 all work.

Helpers used throughout the gallery:

```js
const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
const lerp = (a, b, p) => a + (b - a) * p;
const EC = {}; const ease = n => EC[n] || (EC[n] = gsap.parseEase(n));      // GSAP eases as functions
const prog = (t, a, b, e = 'none') => ease(e)(clamp((t - a) / (b - a)));    // 0..1 progress of a beat
// keyframes [[t, value, ease], ...]; value may be a number or an array
function kf(t, K) {
  if (t <= K[0][0]) return K[0][1];
  for (let i = 1; i < K.length; i++) if (t <= K[i][0]) {
    const [t0, v0] = K[i - 1], [t1, v1, e] = K[i];
    const p = ease(e || 'power1.inOut')((t - t0) / (t1 - t0));
    return Array.isArray(v0) ? v0.map((x, j) => lerp(x, v1[j], p)) : lerp(v0, v1, p);
  }
  return K[K.length - 1][1];
}
const f1 = v => (Math.round(v * 10) / 10).toString();   // short attribute strings, smaller DOM churn
```

`kf` reads like the shot list: `const y = kf(t, [[12.5, 942], [13.15, 935], [13.375, 812, 'power2.out'], ...])`.
Measure the keys on the frames; add a key wherever the frames show a change of direction or speed.

Mixing both is fine (tweens for layout, `draw(t)` for particles) as long as `seek` calls both with the same t.

## Determinism

- `seek(t)` must give the same image whatever was seeked before. `check_anim.py --runtime` tests it.
- No `Math.random()` at draw time: precompute particles with a seeded PRNG in `build()`:
  `const rnd = (s => () => (s = (s * 16807) % 2147483647) / 2147483647)(42);`
- No CSS transitions or keyframe animations on the stage, no `requestAnimationFrame` loop of your own, no
  `setTimeout` choreography. Hover effects belong in `site.html`, not in the replay.
- Spring and bounce settles are closed-form (`elastic.out`, damped sine `A * exp(-k u) * sin(w u)`), not
  simulated step by step.

## Morphs

- Same-structure paths (same commands, same point count) tween directly with `attr: { d }`.
- Different shapes: flubber 0.4.2 from jsdelivr, precomputed once:
  `const f = flubber.interpolate(fromD, toD, { maxSegmentLength: 12 }); path.setAttribute('d', f(p));`
- Circle to rounded square: tween `rx` on a `<rect>`. Blob to puddle: an ellipse whose `rx`/`ry` follow a curve.
- Iris and wipe transitions: animate a `<clipPath>` circle or rect radius, the new scene inside the clip.

## Type

- Closest Google Font, subset to the exact glyphs with `&text=` and `display=block` (no fallback flash in captures):
  `https://fonts.googleapis.com/css2?family=Anton&display=block&text=THINKBG`
- Wait for it before ready: `Promise.race([document.fonts.load('100px "Anton"', 'THINK BIG'), timeout(4000)])`.
- Bubbly sticker letters: `<text>` with a thick stroke and `paint-order="stroke"`, one `<text>` per letter when
  letters pop, bounce or stretch separately (transform origin at the baseline).
- Counters (scores, timers) are computed text: `el.textContent = Math.round(lerp(0, 1000, p))`.

## Size and structure

The gallery replays are 24 to 60 KB of readable code for 10 to 15 s at 1920x1080. Above about 150 KB, look for repeated
drawing that should be a function or `<use>`. Keep: palette constants at the top, `build()` that creates
repeated elements, one function per shot or character, `render(t)` or the timeline in time order, then the
`window.anim` block and the boot code (fonts, `?t=`, `?external=1`, `data-ready`).
