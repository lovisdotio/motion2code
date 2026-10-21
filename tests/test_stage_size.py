#!/usr/bin/env python3
"""Unit tests for _m2c.stage_size (stdlib only).

  python3 tests/test_stage_size.py
"""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "skills" / "motion2code" / "scripts"))
from _m2c import stage_size  # noqa: E402


def size_of(html: str):
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as f:
        f.write(html)
    try:
        return stage_size(f.name)
    finally:
        Path(f.name).unlink()


class StageSize(unittest.TestCase):
    def test_plain_stage(self):
        self.assertEqual(size_of('<svg id="stage" viewBox="0 0 1080 1920"></svg>'), (1080, 1920))

    def test_stage_after_icon_sprite(self):
        html = ('<svg class="icon" viewBox="0 0 24 24"><path d="M0 0"/></svg>'
                '<svg id="stage" viewBox="0 0 1080 1920"></svg>')
        self.assertEqual(size_of(html), (1080, 1920))

    def test_single_quoted_viewbox(self):
        self.assertEqual(size_of("<svg id='stage' viewBox='0 0 1080 1920'></svg>"), (1080, 1920))

    def test_no_stage_id_uses_first_svg(self):
        self.assertEqual(size_of('<svg viewBox="0 0 800 600"></svg>'), (800, 600))

    def test_fallback(self):
        self.assertEqual(size_of("<div></div>"), (1920, 1080))


if __name__ == "__main__":
    unittest.main()
