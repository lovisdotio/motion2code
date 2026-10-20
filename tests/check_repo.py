#!/usr/bin/env python3
"""Repository checks: every gallery page and template passes check_anim.py, and committed text files contain no
absolute home paths, emojis or obvious secrets.

  python3 tests/check_repo.py              # static checks (stdlib only)
  python3 tests/check_repo.py --runtime    # + headless browser checks of every replay (Playwright + ffmpeg)
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "skills" / "motion2code" / "scripts"
TEXT = {".md", ".py", ".html", ".json", ".yaml", ".yml", ".mdc", ".txt"}
EMOJI = re.compile("[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F000-\U0001F2FF]")
SECRET = re.compile(r"(sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|FAL_KEY\s*=\s*\S+|ghp_[A-Za-z0-9]{30,})")
HOME = re.compile(r"/(Users|home)/[A-Za-z0-9_.-]+/")


def main():
    runtime = "--runtime" in sys.argv
    failed = False
    for p in sorted(ROOT.rglob("*")):
        if p.suffix not in TEXT or ".git" in p.parts or p.name == "check_repo.py":
            continue
        s = p.read_text(encoding="utf-8", errors="ignore")
        for name, rx in (("absolute home path", HOME), ("emoji", EMOJI), ("possible secret", SECRET)):
            m = rx.search(s)
            if m:
                failed = True
                print(f"[FAIL] {p.relative_to(ROOT)}: {name}: {m.group(0)[:40]!r}")
    replays = sorted((ROOT / "gallery").glob("*/index.html")) + [ROOT / "skills/motion2code/templates/index.html"]
    sites = sorted((ROOT / "gallery").glob("*/site.html")) + [ROOT / "skills/motion2code/templates/site.html"]
    cmd = [sys.executable, str(SCRIPTS / "check_anim.py"), *map(str, replays)] + (["--runtime"] if runtime else [])
    failed |= subprocess.run(cmd).returncode != 0
    failed |= subprocess.run([sys.executable, str(SCRIPTS / "check_anim.py"), *map(str, sites)]).returncode != 0
    print("FAILED" if failed else "all checks passed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
