# Motion vocabulary: what you see in the frames, what to write

AI motion design clips are fast (a new beat about every second) and lean on a small set of moves. Identify the
move from the frame sequence, then use the matching recipe. Agents tend to default to `power1.inOut` everywhere;
that is the main reason a rebuild feels "floaty" next to the source.

| In the frames | Write |
|---|---|
| Shape jumps to a new size in 1 to 2 frames, then holds | `back.out(2)` to `back.out(3)` over 0.15 to 0.25 s, or `gsap.set` + a 2-frame overshoot |
| Pops in from nothing | scale 0 to 1, `back.out(2.5)`, 0.2 to 0.4 s, transform origin at the contact point |
| Lands and wobbles before settling | squash on contact (`scaleX 1.2, scaleY 0.8` for 2 to 3 frames), then `elastic.out(1, 0.35)` back to 1 |
| Anticipation before a jump | 0.2 to 0.35 s squash with `power2.in`, then stretch along the motion with `power3.out` |
| Smear (stretched blur-free shape on fast moves) | scale along the velocity for the 1 to 3 fastest frames, rotate the group to the motion angle |
| Slides in, decelerates hard | `power3.out` / `expo.out`, 0.3 to 0.5 s |
| Leaves fast | `power2.in` / `back.in(1.7)`, 0.2 to 0.3 s |
| Constant drift (clouds, conveyor, marquee) | `ease: 'none'`, a distance that wraps to the loop (see `seamless-loop.md`) |
| Stagger of letters or items | `stagger: 0.06` to `0.12`, from the side the source starts |
| Color flood / wave across the frame | a big shape (circle, blob path) scaling from its origin, or a clipPath growing; the old scene stays below |
| Iris to a new scene | `<clipPath>` circle radius 0 to diagonal (1100 px for 1920x1080), `power2.in` closing, `power2.out` opening |
| One shape turns into another | morph (`attr: d` or flubber) while moving; the beat linking rule of AI loops |
| Blink | lids: scaleY 1 to 0.1 to 1 over 4 to 5 frames, every 2 to 4 s, at times read from the frames |
| Hard stop on a punchline | linear or `power4.out` into a hold; nothing moves for 0.3 to 0.6 s |
| Number counting up | text from `Math.round(lerp(a, b, prog(t, t0, t1, 'power2.out')))` |
| Bounce series | separate keys per bounce with `power2.out` up and `power2.in` down, heights losing about 40 % each |

## Measure, then pick

- Count the frames a move takes (at 24 fps, 3 frames = 0.125 s). Snappy AI moves are often 3 to 6 frames.
- Track one point (a center, an eye, a corner) across the 0.25 s frames and write its positions down. If the
  distance between frames shrinks fast, it is an `out` ease; if it grows, `in`; if it overshoots, `back`.
- When unsure, extract the transition at full frame rate with
  `python3 scripts/frame_diff.py source.mp4 index.html -o d/ --every 1/24 --start 6.8 --end 7.4` and compare
  your curve frame by frame.

## Squash and stretch rules

- Keep the area roughly constant: `scaleY = 1 / scaleX` within about 10 %.
- Scale around the contact point (bottom center for a character on the floor, rim for a cup) by drawing the
  object around that origin.
- Faces ride along: eyes and mouth are children of the body group, so they squash with it, then settle a frame
  later for a bit of drag if the source shows it.
