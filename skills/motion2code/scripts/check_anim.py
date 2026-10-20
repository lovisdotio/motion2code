#!/usr/bin/env python3
"""Check a coded animation against the motion2code contract.

  python3 check_anim.py index.html                 # static checks only (stdlib, no browser)
  python3 check_anim.py index.html --runtime       # + headless browser checks (Playwright + ffmpeg)
  python3 check_anim.py gallery/*/index.html --runtime

Static (errors fail):
  - window.anim exposes duration, seek, play, pause; data-ready is set; ?external=1 and ?t= are handled
  - scripts only from the allowlist (GSAP 3 on cdnjs, flubber on jsdelivr); fonts only from Google Fonts
  - no raster or video in the animation: no <img>, <video>, <canvas> drawImage, SVG <image>, url(...png), data:image/png
  - warnings: Math.random / Date.now / performance.now (seek must be a pure function of t)
Runtime (--runtime):
  - zero console errors, no request outside the allowlist, anim.duration is a positive number
  - loop seam: frame at t=0 vs t=duration must match (mean diff < --seam), and t=0 vs the last frame before the
    wrap (duration - 1/fps) must be close (< --seam-step): no jump when the timeline restarts
  - determinism: seeking to the same t after other seeks gives the same image (no hidden state)
  - autoplay: opened without parameters the page plays on its own
Exit code 1 when any error is found.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _m2c import image_rgb, launch, mean_abs_diff, open_anim, parse_size, playwright, seek_shot, serve  # noqa: E402

SCRIPT_ALLOW = [
    "https://cdnjs.cloudflare.com/ajax/libs/gsap/3.",
    "https://cdn.jsdelivr.net/npm/flubber@",
]
HOST_ALLOW = {"cdnjs.cloudflare.com", "cdn.jsdelivr.net", "fonts.googleapis.com", "fonts.gstatic.com"}


def static_check(path: Path, extra_allow: list[str], site: bool) -> tuple[list[str], list[str]]:
    s = path.read_text(encoding="utf-8", errors="ignore")
    err, warn = [], []
    code = re.sub(r"<!--.*?-->", "", s, flags=re.S)
    if not site:
        if "window.anim" not in code:
            err.append("window.anim is not defined")
        for k in ("duration", "seek", "play", "pause"):
            if not re.search(rf"\b{k}\b", code):
                err.append(f"window.anim.{k} not found")
        if not re.search(r"dataset\.ready|data-ready|setAttribute\(\s*['\"]data-ready", code):
            err.append("data-ready is never set on <html> (renderers wait for it)")
        if "external" not in code:
            err.append("?external=1 is not handled (compare.html and renderers need the page not to autoplay)")
        if not re.search(r"""(get|has)\(\s*['"]t['"]\s*\)""", code):
            warn.append("?t= (freeze at a time) is not handled")
        if not re.search(r"gsap\.timeline|gsap\.to|gsap\.fromTo", code):
            err.append("no GSAP timeline: GSAP must be the single clock")
        if re.search(r"requestAnimationFrame\s*\(\s*(loop|tick|animate|render)\b", code):
            warn.append("a requestAnimationFrame loop drives something besides GSAP: it will ignore seek(t)")
        if re.search(r"\bsetInterval\s*\(|\bsetTimeout\s*\([^)]*\b(tl|gsap|anim)\b", code):
            warn.append("setInterval/setTimeout timing does not follow seek(t)")
    for src in re.findall(r"<script[^>]+src=[\"']([^\"']+)", code, flags=re.I):
        if src.startswith(("http:", "https:", "//")) and not any(src.startswith(p) for p in SCRIPT_ALLOW + extra_allow):
            err.append(f"external script not allowed: {src}")
    for href in re.findall(r"<link[^>]+href=[\"']([^\"']+)", code, flags=re.I):
        if href.startswith(("http:", "https:", "//")):
            host = urlparse(href if not href.startswith("//") else "https:" + href).hostname
            if host not in ("fonts.googleapis.com", "fonts.gstatic.com") and not any(href.startswith(p) for p in extra_allow):
                err.append(f"external stylesheet/link not allowed: {href}")
    raster = [(r"<img\b", "<img>"), (r"<video\b", "<video>"), (r"<image\b", "SVG <image>"), (r"\bdrawImage\s*\(", "canvas drawImage"),
              (r"url\(\s*['\"]?[^)'\"]+\.(png|jpe?g|webp|gif|avif)", "CSS url() raster"),
              (r"data:image/(png|jpe?g|webp|gif|avif)", "embedded raster data URI")]
    for pat, name in raster:
        if re.search(pat, code, flags=re.I):
            err.append(f"raster/video asset in the animation: {name} (redraw it as flat SVG shapes)")
    for pat, name in [(r"Math\.random\s*\(", "Math.random()"), (r"Date\.now\s*\(", "Date.now()"),
                      (r"performance\.now\s*\(", "performance.now()")]:
        if re.search(pat, code) and not site:
            warn.append(f"{name} found: make it seeded/precomputed so seek(t) is a pure function of t")
    if re.search(r"/(Users|home)/[A-Za-z0-9_.-]+/", s):
        err.append("absolute personal path found in the file")
    return err, warn


def runtime_check(browser, path: Path, base: str, root: Path, size, fps: float, seam: float, seam_step: float,
                  extra_allow: list[str]) -> tuple[list[str], list[str], dict]:
    err, warn, stats = [], [], {}
    errors, requests = [], []
    try:
        page, dur = open_anim(browser, path, base, root, size, errors=errors, requests=requests)
    except Exception as e:  # noqa: BLE001
        return [f"page never set data-ready (or failed to load): {e}"], warn, stats
    if not isinstance(dur, (int, float)) or dur <= 0:
        return ["window.anim.duration is not a positive number"], warn, stats
    api = page.evaluate("() => ['seek','play','pause'].filter(k => typeof window.anim[k] !== 'function')")
    if api:
        err.append(f"window.anim functions missing: {api}")
        return err, warn, stats
    W, H = 192, int(192 * size[1] / size[0])
    rgb = lambda png: image_rgb(png, W, H)  # noqa: E731
    f0 = rgb(seek_shot(page, 0))
    fend = rgb(seek_shot(page, dur))
    flast = rgb(seek_shot(page, dur - 1 / fps))
    fmid = rgb(seek_shot(page, dur * 0.5))
    seek_shot(page, dur * 0.83)
    seek_shot(page, dur * 0.11)
    fmid2 = rgb(seek_shot(page, dur * 0.5))
    stats = {"duration": dur, "seam_end": round(mean_abs_diff(f0, fend), 2),
             "seam_last_frame": round(mean_abs_diff(f0, flast), 2),
             "determinism": round(mean_abs_diff(fmid, fmid2), 2), "start_vs_mid": round(mean_abs_diff(f0, fmid), 2)}
    if stats["seam_end"] > seam:
        err.append(f"loop seam: frame at t=duration differs from t=0 (mean diff {stats['seam_end']} > {seam})")
    if stats["seam_last_frame"] > seam_step:
        err.append(f"loop jump: last frame before the wrap differs from t=0 (mean diff {stats['seam_last_frame']} > {seam_step})")
    if stats["determinism"] > 0.5:
        err.append(f"seek is not deterministic: same t, different image after other seeks (diff {stats['determinism']})")
    if stats["start_vs_mid"] < 0.5:
        warn.append("frame at mid-duration equals frame 0: is anything animating?")
    page.close()
    # autoplay without parameters
    page2 = browser.new_page(viewport={"width": size[0], "height": size[1]})
    page2.on("console", lambda m: m.type == "error" and errors.append(m.text))
    page2.on("pageerror", lambda e: errors.append(str(e)))
    page2.on("request", lambda r: requests.append(r.url))
    rel = path.resolve().relative_to(root.resolve()).as_posix()
    page2.goto(f"{base}/{rel}")
    try:
        page2.wait_for_function("document.documentElement.dataset.ready === '1'", timeout=20000)
        t1 = page2.evaluate("window.anim.tl ? window.anim.tl.time() : null")
        page2.wait_for_timeout(600)
        t2 = page2.evaluate("window.anim.tl ? window.anim.tl.time() : null")
        if t1 is not None and t2 is not None and t2 == t1:
            err.append("opened without parameters the timeline does not play")
        elif t1 is None:
            a = rgb(page2.screenshot()); page2.wait_for_timeout(600); b = rgb(page2.screenshot())
            if mean_abs_diff(a, b) < 0.2:
                warn.append("opened without parameters nothing moved in 0.6 s (autoplay?)")
    except Exception as e:  # noqa: BLE001
        err.append(f"autoplay page failed: {e}")
    page2.close()
    for e in errors:
        err.append(f"console error: {e[:200]}")
    for u in requests:
        host = urlparse(u).hostname
        if u.startswith(("http:", "https:")) and host not in ("127.0.0.1", "localhost") and host not in HOST_ALLOW \
                and not any(u.startswith(p) for p in extra_allow):
            err.append(f"request outside the allowlist: {u}")
    return err, warn, stats


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("html", nargs="+")
    ap.add_argument("--runtime", action="store_true", help="also open each page in headless Chromium")
    ap.add_argument("--site", action="store_true", help="interactive site.html: skip the window.anim contract")
    ap.add_argument("--fps", type=float, default=24)
    ap.add_argument("--seam", type=float, default=1.0, help="max mean diff between t=0 and t=duration (0..255)")
    ap.add_argument("--seam-step", type=float, default=8.0, help="max mean diff between t=0 and duration-1/fps")
    ap.add_argument("--size", help="viewport WxH (default from the svg viewBox)")
    ap.add_argument("--allow", action="append", default=[], help="extra allowed URL prefix (repeatable)")
    ap.add_argument("--root", help="folder to serve (default: each page's folder)")
    a = ap.parse_args()
    failed = 0
    pw = browser = ctx = None
    if a.runtime:
        ctx = playwright()()
        pw = ctx.__enter__()
        browser = launch(pw)
    try:
        for h in a.html:
            path = Path(h)
            site = a.site or path.name.startswith("site")
            err, warn = static_check(path, a.allow, site)
            stats = {}
            if a.runtime and not site and not err:
                root = Path(a.root).resolve() if a.root else path.resolve().parent
                httpd, base = serve(root)
                try:
                    e2, w2, stats = runtime_check(browser, path, base, root, parse_size(a.size, path), a.fps,
                                                  a.seam, a.seam_step, a.allow)
                finally:
                    httpd.shutdown()
                err += e2; warn += w2
            status = "FAIL" if err else "ok"
            failed += bool(err)
            extra = "  " + "  ".join(f"{k}={v}" for k, v in stats.items()) if stats else ""
            print(f"[{status}] {h}{extra}")
            for e in err:
                print(f"   error: {e}")
            for w in warn:
                print(f"   warn:  {w}")
    finally:
        if browser:
            browser.close()
            ctx.__exit__(None, None, None)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
