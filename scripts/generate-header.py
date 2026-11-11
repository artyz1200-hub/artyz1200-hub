#!/usr/bin/env python3
"""Render the neon title and the Seoul skyline into assets/.

Neither depends on contribution data, so run this by hand and commit the output.
"""
from __future__ import annotations

from pathlib import Path

from neon.header import skyline_svg, title_svg

ASSETS = Path(__file__).resolve().parent.parent / "assets"


def main():
    ASSETS.mkdir(exist_ok=True)
    for name, make in (("title.svg", title_svg), ("seoul-skyline.svg", skyline_svg)):
        path = ASSETS / name
        data = make()
        path.write_text(data, encoding="utf-8")
        print(f"Wrote {path} ({len(data) // 1024} KB)")


if __name__ == "__main__":
    main()
