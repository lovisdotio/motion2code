"""Shared helpers for the motion2code scripts (stdlib only; ffmpeg/ffprobe on PATH; Playwright imported lazily)."""
from __future__ import annotations

import functools
import http.server
import json
import os
import re
import shutil
import socketserver
import subprocess
import sys
import threading
from pathlib import Path


def die(msg: str, code: int = 1):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)


def need(tool: str):
    if not shutil.which(tool):
        die(f"`{tool}` not found on PATH (install ffmpeg: brew install ffmpeg / apt install ffmpeg)")


# ---------------------------------------------------------------- video

def probe(path: str | Path) -> dict:
    """Width, height, fps, duration and frame count of a video."""
    need("ffprobe")
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
         "stream=width,height,r_frame_rate,nb_frames:format=duration", "-of", "json", str(path)],
        capture_output=True, text=True, check=True).stdout
    d = json.loads(out)
    s = d["streams"][0]
    num, den = (s.get("r_frame_rate") or "24/1").split("/")
    fps = float(num) / float(den or 1)
    dur = float(d["format"]["duration"])
    return {"width": int(s["width"]), "height": int(s["height"]), "fps": round(fps, 3),
            "duration": round(dur, 3), "frames": int(s.get("nb_frames") or round(dur * fps))}


def _ff_raw(args: list[str], w: int, h: int, last: bool = False) -> bytes:
    need("ffmpeg")
    out = subprocess.run(["ffmpeg", "-v", "error", *args, "-vf", f"scale={w}:{h}:flags=area",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    n = w * h * 3
    if len(out) < n:
        return b""
    return out[-n:] if last else out[:n]


def video_frame_rgb(video: str | Path, t: float, w: int = 160, h: int = 90) -> bytes:
    """One frame of `video` at time t (seconds) as raw RGB bytes of size w*h*3.
    Times at or past the end return the last frame (seeking with -sseof, never -ss past the end)."""
    info = probe(video)
    if t >= info["duration"] - 1.5 / info["fps"]:
        return _ff_raw(["-sseof", "-0.5", "-i", str(video)], w, h, last=True)
    data = _ff_raw(["-ss", f"{max(0.0, t):.4f}", "-i", str(video), "-frames:v", "1"], w, h)
    return data or _ff_raw(["-sseof", "-0.5", "-i", str(video)], w, h, last=True)


def image_rgb(png: bytes | str | Path, w: int = 160, h: int = 90) -> bytes:
    """Decode an image (bytes or path) to raw RGB at w*h via ffmpeg."""
    need("ffmpeg")
    if isinstance(png, (str, Path)):
        return _ff_raw(["-i", str(png)], w, h)
    out = subprocess.run(["ffmpeg", "-v", "error", "-f", "image2pipe", "-i", "-", "-vf", f"scale={w}:{h}:flags=area",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], input=png, capture_output=True).stdout
    return out[: w * h * 3]


def mean_abs_diff(a: bytes, b: bytes) -> float:
    """Mean absolute per-channel difference, 0 (identical) .. 255."""
    if not a or not b or len(a) != len(b):
        return float("nan")
    return sum(abs(x - y) for x, y in zip(a, b)) / len(a)


def save_frame_png(video: str | Path, t: float, out: str | Path, width: int | None = None):
    need("ffmpeg")
    info = probe(video)
    vf = ["-vf", f"scale={width}:-2"] if width else []
    if t >= info["duration"] - 1.5 / info["fps"]:
        args = ["-sseof", "-0.5", "-i", str(video), "-update", "1"]
    else:
        args = ["-ss", f"{max(0.0, t):.4f}", "-i", str(video), "-frames:v", "1"]
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args, *vf, str(out)], check=True)


# ---------------------------------------------------------------- local server + browser

class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def serve(directory: str | Path):
    """Serve `directory` on 127.0.0.1 on a free port in a daemon thread. Returns (server, base_url)."""
    handler = functools.partial(_Quiet, directory=str(directory))
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.ThreadingTCPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, f"http://127.0.0.1:{httpd.server_address[1]}"


def playwright():
    try:
        from playwright.sync_api import sync_playwright  # noqa
    except ImportError:
        die("Playwright is missing. Run with `uv run --with playwright python ...` "
            "or `pip install playwright && python -m playwright install chromium`.")
    return sync_playwright


def launch(p):
    """Installed Chrome first (fast, no download), then Playwright's bundled Chromium."""
    for kw in ({"channel": "chrome"}, {}):
        try:
            return p.chromium.launch(**kw)
        except Exception:
            continue
    die("could not launch Chromium (try `python -m playwright install chromium`)")


def stage_size(html: str | Path) -> tuple[int, int]:
    """Stage size from the first <svg viewBox> (falls back to 1920x1080)."""
    txt = Path(html).read_text(encoding="utf-8", errors="ignore")
    m = re.search(r'<svg[^>]*viewBox="\s*[-\d.]+[\s,]+[-\d.]+[\s,]+([\d.]+)[\s,]+([\d.]+)', txt)
    return (int(float(m.group(1))), int(float(m.group(2)))) if m else (1920, 1080)


def parse_size(s: str | None, html: str | Path) -> tuple[int, int]:
    if s:
        w, h = s.lower().split("x")
        return int(w), int(h)
    return stage_size(html)


def open_anim(browser, html: Path, base_url: str, root: Path, size: tuple[int, int], query: str = "external=1",
              errors: list | None = None, requests: list | None = None, timeout_ms: int = 20000):
    """Open html (under `root`, served at base_url) and wait for data-ready. Returns (page, duration)."""
    page = browser.new_page(viewport={"width": size[0], "height": size[1]}, device_scale_factor=1)
    if errors is not None:
        page.on("console", lambda m: m.type == "error" and errors.append(m.text))
        page.on("pageerror", lambda e: errors.append(str(e)))
    if requests is not None:
        page.on("request", lambda r: requests.append(r.url))
    rel = html.resolve().relative_to(root.resolve()).as_posix()
    page.goto(f"{base_url}/{rel}" + (f"?{query}" if query else ""), wait_until="load")
    page.wait_for_function("document.documentElement.dataset.ready === '1'", timeout=timeout_ms)
    dur = page.evaluate("window.anim && window.anim.duration")
    return page, dur


def seek_shot(page, t: float, path: str | Path | None = None) -> bytes:
    page.evaluate("t => window.anim.seek(t)", t)
    page.evaluate("() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))")
    return page.screenshot(path=str(path) if path else None, type="png")


def human_kb(path: str | Path) -> str:
    return f"{os.path.getsize(path) / 1024:.0f} KB"
