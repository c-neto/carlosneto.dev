#!/usr/bin/env python3
"""Export GoatCounter stats to ``_static/analytics.json`` for the public /analytics page.

Runs hourly in CI (.github/workflows/analytics.yml), which commits the JSON
straight to the gh-pages branch without rebuilding the site. Needs the
``GOATCOUNTER_TOKEN`` env var (an API key with "read statistics" permission).
Without it, or when the API fails, the script only warns and writes nothing,
so the last published JSON stays online.

Only blog posts are counted (see POST_PATH): the home, listing and other
pages are filtered out with the API's include_paths. Only aggregated data is
exported: totals, posts, countries, referrers, browsers, systems and screen
sizes. GoatCounter stores no IPs or cookies.
"""

import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

SITE = os.environ.get("GOATCOUNTER_SITE", "https://c-neto.goatcounter.com")
# GOATCOUNTER_OUT lets CI write straight into a gh-pages checkout.
OUT = Path(
    os.environ.get("GOATCOUNTER_OUT")
    or Path(__file__).resolve().parent.parent / "_static" / "analytics.json"
)
RANGES = {"30d": 30, "365d": 365}
# Blog posts only, e.g. /blog/2025/2025-06-19-fluentbit-log-dedup/.
# Listing pages (/blog/, tags, categories, archives) are left out.
POST_PATH = re.compile(r"^/blog/\d{4}/\d{4}-\d{2}-\d{2}-[^/]+/?$")
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


def all_hits(token: str, start: str, end: str) -> list[dict]:
    """Every path with visits in the range. The API pages with exclude_paths."""
    hits, seen = [], []
    while True:
        data = get(
            "stats/hits", token, start=start, end=end, limit=100, exclude_paths=seen
        )
        page = data.get("hits") or []
        hits.extend(page)
        seen.extend(str(h["path_id"]) for h in page)
        if not data.get("more") or not page:
            return hits


def stat_list(page: str, token: str, start: str, end: str, path_ids: list[str]) -> list[dict]:
    data = get(
        f"stats/{page}", token, start=start, end=end, limit=LIMIT, include_paths=path_ids
    )
    return [
        {"id": s.get("id") or "", "name": s.get("name") or "", "count": s.get("count", 0)}
        for s in data.get("stats") or []
    ]


def empty_days(start_dt: datetime, end_dt: datetime) -> list[dict]:
    days = (end_dt.date() - start_dt.date()).days + 1
    return [{"day": str(start_dt.date() + timedelta(days=i)), "count": 0} for i in range(days)]


def export_range(token: str, days: int, now: datetime) -> dict:
    end_dt = now.replace(minute=0, second=0, microsecond=0)
    start_dt = (end_dt - timedelta(days=days - 1)).replace(hour=0)
    start = start_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    end = end_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    # Only blog posts count: every other stat is filtered to their path IDs.
    posts = sorted(
        (h for h in all_hits(token, start, end)
         if not h.get("event") and POST_PATH.match(h.get("path", ""))),
        key=lambda h: h.get("count", 0),
        reverse=True,
    )
    result = {
        "start": start,
        "end": end,
        "posts": len(posts),
        "pages": [
            {"path": h["path"], "title": h.get("title") or "", "count": h.get("count", 0)}
            for h in posts[:LIMIT]
        ],
    }

    # An empty include_paths means "everything" to the API, so skip the calls.
    if not posts:
        result.update(total=0, daily=empty_days(start_dt, end_dt))
        result.update({key: [] for key in STAT_PAGES})
        return result

    ids = [str(h["path_id"]) for h in posts]
    total = get("stats/total", token, start=start, end=end, include_paths=ids)
    result["total"] = total.get("total", 0)
    result["daily"] = [
        {"day": s["day"], "count": s.get("daily", 0)} for s in total.get("stats") or []
    ]
    for key, page in STAT_PAGES.items():
        result[key] = stat_list(page, token, start, end, ids)

    # Sanity check for the include_paths encoding: the filtered total can never
    # be below the busiest single post.
    if result["total"] < posts[0].get("count", 0):
        raise ValueError("filtered total is below the top post; include_paths was not applied")
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
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
    r30 = ranges["30d"]
    print(f"Wrote {OUT} ({r30['total']} visitors on {r30['posts']} posts in the last 30 days)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
