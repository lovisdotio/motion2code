# AGENTS.md

Guidance for coding agents (Claude Code, Codex, Cursor, Copilot, Gemini) working on this repository. To use the
skill rather than develop it, see the README.

## Layout

```text
skills/motion2code/            the skill (this is what gets installed)
  SKILL.md                     entry point: workflow, page contract, hard rules, reference routing
  references/                  study, architecture, motion vocabulary, loop, verification, interfaces and sites
  scripts/                     study_video, palette, render_anim, frame_diff, side_by_side, check_anim (+ _m2c helpers)
  templates/                   index.html (contract), compare.html (video vs code), site.html (ScrollTrigger)
  agents/openai.yaml           Codex display metadata
gallery/<name>/                index.html replay, compare.html, source.mp4 (480p), poster.gif, site.html for interfaces
prompts/                       fill-in conversion prompt, source prompt advice
adapters/                      copy-in prompts for tools without skill support
tests/check_repo.py            checks every gallery page and template, plus repo hygiene
.claude-plugin/                Claude Code plugin + marketplace manifests
```

## Commands

```bash
python3 tests/check_repo.py                                    # static checks (stdlib only)
uv run --with playwright python tests/check_repo.py --runtime  # + headless seam/determinism/console checks
```

## Rules

- Scripts: Python 3.9+ standard library, ffmpeg/ffprobe on PATH, Playwright imported only where a browser is
  needed. No Pillow, no numpy. Every script has a docstring with usage lines and `--help`.
- Gallery pages must pass `check_anim.py --runtime`: contract, loop seam, determinism, zero console errors, no
  request outside the allowlist.
- A new gallery entry: `index.html` + `compare.html` (the template, unchanged) + `source.mp4` re-encoded to 480p
  without audio + `poster.gif` (4 to 5 s, 480 px wide, under 700 KB) + a row in the README table. Keep the repo
  under 30 MB.
- No absolute home paths, emojis, secrets or API keys in committed files. Code comments in English.
