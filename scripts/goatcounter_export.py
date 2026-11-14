#!/usr/bin/env python3
"""Export GoatCounter stats to ``_static/analytics.json`` for the public /analytics page.

Runs in CI before the Sphinx build. Needs the ``GOATCOUNTER_TOKEN`` env var
(an API key with "read statistics" permission). Without it, or when the API
fails, the script only warns: the site still deploys and the page shows its
"no data yet" state.

Only aggregated data is exported: totals, pages, countries, referrers,
browsers, systems and screen sizes. GoatCounter stores no IPs or cookies.
"""

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

SITE = os.environ.get("GOATCOUNTER_SITE", "https://c-neto.goatcounter.com")
OUT = Path(__file__).resolve().parent.parent / "_static" / "analytics.json"
RANGES = {"30d": 30, "365d": 365}
LIMIT = 10
STAT_PAGES = {
    "countries": "locations",
    "referrers": "toprefs",
    "browsers": "browsers",
    "systems": "systems",
    "sizes": "sizes",
}


def warn(msg: str) -> None:
    # "::warning::" shows up as an annotation in the GitHub Actions run.
    print(f"::warning::{msg}", file=sys.stderr)


def get(endpoint: str, token: str, **params) -> dict:
    url = f"{SITE}/api/v0/{endpoint}?{urllib.parse.urlencode(params, doseq=True)}"
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    for attempt in range(3):
        time.sleep(0.3)  # API limit is 4 requests per second.
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as err:
            if err.code == 429 and attempt < 2:
                time.sleep(int(err.headers.get("X-Rate-Limit-Reset", "1")) + 1)
                continue
            raise
    raise RuntimeError(f"giving up on {endpoint}")


def stat_list(page: str, token: str, start: str, end: str) -> list[dict]:
    data = get(f"stats/{page}", token, start=start, end=end, limit=LIMIT)
    return [
        {"id": s.get("id") or "", "name": s.get("name") or "", "count": s.get("count", 0)}
        for s in data.get("stats") or []
    ]


def export_range(token: str, days: int, now: datetime) -> dict:
    end_dt = now.replace(minute=0, second=0, microsecond=0)
    start_dt = (end_dt - timedelta(days=days - 1)).replace(hour=0)
    start = start_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    end = end_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    total = get("stats/total", token, start=start, end=end)
    hits = get("stats/hits", token, start=start, end=end, limit=LIMIT)

    result = {
        "start": start,
        "end": end,
        "total": total.get("total", 0),
        "daily": [
            {"day": s["day"], "count": s.get("daily", 0)} for s in total.get("stats") or []
        ],
        "pages": [
            {"path": h.get("path", ""), "title": h.get("title") or "", "count": h.get("count", 0)}
            for h in hits.get("hits") or []
            if not h.get("event")
        ],
    }
    for key, page in STAT_PAGES.items():
        result[key] = stat_list(page, token, start, end)
    return result


def main() -> int:
    token = os.environ.get("GOATCOUNTER_TOKEN", "").strip()
    if not token:
        warn("GOATCOUNTER_TOKEN is not set; skipping analytics export.")
        return 0

    now = datetime.now(timezone.utc)
    try:
        ranges = {key: export_range(token, days, now) for key, days in RANGES.items()}
    except (urllib.error.URLError, RuntimeError, KeyError, ValueError) as err:
        warn(f"GoatCounter export failed: {err}")
        return 0

    payload = {"generated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "ranges": ranges}
    OUT.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
    print(f"Wrote {OUT} ({ranges['30d']['total']} visitors in the last 30 days)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
