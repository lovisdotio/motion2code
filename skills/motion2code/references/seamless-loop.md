# Seamless loop

The coded animation must loop perfectly: the frame at `t = duration` is the frame at `t = 0`, and nothing jumps
when the timeline wraps. This is required even when the source video does not loop. Never look for or generate
another version of the source to get a loop: the loop is done in code.

## Does the source loop?

`study_video.py` prints `source first/last frame diff`. Under about 6 (0..255 mean difference at 160x90) the
source returns to its opening frame and you only need to reproduce it. Above that, plan a return.

## Define the opening frame once

Keep the opening state in one place (an `OPEN` object, or the reset block at the top of `render(t)`). The last
shot animates to exactly those values. Do not hand-copy numbers twice: a 2 px difference shows as a jump.

## Adding the return when the source does not loop

- Keep the source timing for the whole clip, and use its last 0.6 to 1.2 s for the return. If the source ends on
  a hold, the return replaces the hold. If it ends mid-action, choose the move the clip already uses (an iris
  closing on the opening scene, the last shape morphing into the first, everything snapping back with
  `back.out`), so the return looks designed, not appended.
- End with a hold of a few frames on the opening frame: it hides the wrap and matches how AI loops "land".
- Rotations: tween to 360, then `set` rotation 0 at the end (visually identical, numerically exact).
- Drifts (clouds, marquees, scrolling patterns): make the distance travelled over the whole duration an exact
  multiple of the pattern period, so position(duration) = position(0) + period.
- Time-based cycles (blinks, pulses, wobbles): use periods that divide the duration (15 s: 0.5, 0.75, 1, 1.25,
  1.5, 2.5, 3, 3.75, 5 s), or fade their amplitude to 0 before the end.
- Particles alive at the end must be the ones alive at the start (or none at either end).

## Repeated cycles in the source

AI clips often show the same action twice with slightly different tempo. Write the cycle once as a function of
local time and map source time into it with a time warp:

```js
if (t >= 1.0 && t < 6.625) cycle(t - 1.0);
else if (t >= 6.625 && t < 12.5) cycle(kf(t, B_WARP));   // B_WARP maps the second pass onto the first
```

## Check it

```bash
python3 scripts/check_anim.py index.html --runtime
```

It fails when `frame(duration)` differs from `frame(0)` (mean diff over 1.0) or when the last frame before the
wrap (`duration - 1/24`) differs from `frame(0)` by more than 8. Then look at it: render the last second and the
first second next to each other,

```bash
python3 scripts/render_anim.py index.html --png 14.875 14.917 14.958 0 0.042 0.083 --frames-dir seam/
```

and play `index.html` with no parameter through the wrap a few times.
