#!/usr/bin/env python3
"""Build the animated neon contribution city.

Reads the last year's contribution calendar from GitHub GraphQL and writes
dist/contribution-city.svg. Standard library only; needs GITHUB_TOKEN.

    python scripts/generate-city.py            # real data
    python scripts/generate-city.py --demo     # offline preview with fake data
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from neon.city import build
from neon.github import demo_calendar, fetch_calendar

USERNAME = "artyz1200-hub"
OUTPUT = Path("dist/contribution-city.svg")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--demo", action="store_true", help="use generated sample data")
    parser.add_argument("--from-json", type=Path, help='file shaped {"total": n, "days": [...]}')
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--png", type=Path, help="also write an upscaled PNG preview here")
    args = parser.parse_args()

    if args.demo:
        days, total = demo_calendar()
    elif args.from_json:
        data = json.loads(args.from_json.read_text(encoding="utf-8"))
        days, total = data["days"], int(data["total"])
    else:
        days, total = fetch_calendar(USERNAME)

    svg, preview = build(days, total)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(svg, encoding="utf-8")
    if args.png:
        args.png.write_bytes(preview.scaled_png(3))
    print(f"Wrote {args.output} ({len(days)} days, {total} contributions, {len(svg) // 1024} KB).")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
