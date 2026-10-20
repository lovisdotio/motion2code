# Writing source prompts that convert well

Any flat motion clip can be rebuilt, but some videos are much easier to rebuild faithfully. When you generate the
source yourself (the gallery used MiniMax H3 Max text-to-video on fal), these habits help:

- **Flat only.** "Every shape is one solid flat color: no shadows, no shading, no highlights, no gradients, no
  textures." Each extra effect is something the code must fake or drop.
- **No camera language.** Do not write "3D", "camera", "zoom", "pan" or "cut". Describe what the shapes do: they
  slide, grow, split, merge, morph, wipe. Shapes map to SVG; camera moves map to guesses.
- **Linked beats.** "The last shape of each moment becomes the first shape of the next." Chains of morphs and
  wipes are easy to time from the frames and read as one continuous film.
- **Second by second.** Give a time range per beat ("0.0-0.8 s: a white almond eye shape opens"). The shot list
  then almost writes itself, and you can check the video against your own timing.
- **Exact words, few of them.** "Every word is spelled exactly as written and no other words appear." Short
  uppercase words in a bold sans-serif match Google Fonts well.
- **Loop.** "At the end everything returns exactly to the opening frame, so the film loops seamlessly." The video
  will not always obey; the code loops anyway, but a source that loops needs no invented return.
- **Small palette.** Name 3 to 4 colors. Palettes sample cleanly and stay stable across the clip.
- **Interfaces.** "A single continuous screen recording of a real, working website, no browser chrome, small
  round cursor, running text shown as rows of thin flat bars, the only readable words are ..." gives a replay
  that can also become a real site.

Example (the source of `gallery/eye`, abridged):

> Award-winning flat 2D kinetic typography and motion design: bold sans-serif words and only basic geometric
> shapes, solid flat colors, no gradients, no shadows, no textures. Twelve shots in ten seconds, and every
> single transition is linked. Palette: black, white and electric blue. 0.0-0.8 s: a white almond eye shape
> opens. 0.8-1.7 s: the pupil is a blue circle. 1.7-2.5 s: the pupil becomes the O of "LOOK". ...
> 9.2-10.0 s: the eye closes into a line. Snappy easing with anticipation, overshoot and squash. Every word is
> spelled exactly as written and no other words appear.
