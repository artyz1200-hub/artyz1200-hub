"""Fetch the last year's contribution calendar from the GitHub GraphQL API."""
from __future__ import annotations

import json
import os
import urllib.request
from datetime import date, datetime, timedelta, timezone

LEVELS = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2,
          "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}

QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount contributionLevel } }
      }
    }
  }
}"""


def fetch_calendar(login: str) -> tuple[list[dict], int]:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN is not set (use --demo for an offline preview).")
    end = date.today()
    start = end - timedelta(days=364)
    body = json.dumps({"query": QUERY, "variables": {
        "login": login,
        "from": datetime.combine(start, datetime.min.time(), timezone.utc).isoformat(),
        "to": datetime.combine(end, datetime.max.time(), timezone.utc).isoformat(),
    }}).encode()
    req = urllib.request.Request("https://api.github.com/graphql", data=body, method="POST", headers={
        "Authorization": f"Bearer {token}", "Content-Type": "application/json",
        "User-Agent": "neon-seoul-profile"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode())
    if result.get("errors"):
        raise RuntimeError(json.dumps(result["errors"], indent=2))
    user = (result.get("data") or {}).get("user")
    if not user:
        raise RuntimeError(f"GitHub user {login!r} not found.")
    cal = user["contributionsCollection"]["contributionCalendar"]
    days = [{"date": d["date"], "count": int(d["contributionCount"]),
             "level": LEVELS.get(d["contributionLevel"], 0)}
            for w in cal["weeks"] for d in w["contributionDays"]]
    return days, int(cal["totalContributions"])


def demo_calendar(seed: int = 7) -> tuple[list[dict], int]:
    """Plausible fake data for local previews."""
    from .pixels import hash01, fbm1
    end = date.today()
    days, total = [], 0
    for i in range(365):
        d = end - timedelta(days=364 - i)
        busy = fbm1(i / 20, seed) * (0.6 if d.weekday() >= 5 else 1.0)
        r = hash01(i, 0, seed)
        count = 0 if r > busy * 1.3 else int(1 + hash01(i, 1, seed) * busy * 14)
        level = 0 if count == 0 else 1 if count < 3 else 2 if count < 6 else 3 if count < 9 else 4
        days.append({"date": d.isoformat(), "count": count, "level": level})
        total += count
    return days, total
