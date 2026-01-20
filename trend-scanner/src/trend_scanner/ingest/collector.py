from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from time import sleep
from typing import Any

import requests


@dataclass(frozen=True)
class RedditPost:
    external_id: str
    subreddit: str
    author: str
    title: str
    body: str
    score: int
    num_comments: int
    url: str
    created_at: datetime


def _utc_from_ts(ts: float) -> datetime:
    return datetime.fromtimestamp(ts, tz=timezone.utc).replace(tzinfo=None)


def _safe_int(x: Any, default: int = 0) -> int:
    try:
        return int(x)
    except Exception:
        return default


def fetch_new_posts(user_agent: str, subreddits: list[str], limit: int) -> list[RedditPost]:
    """
    Read-only ingestion via public JSON endpoints:
      https://www.reddit.com/r/<sub>/new.json?limit=<N>
    We keep it gentle: small sleep between requests + clear UA.
    """
    headers = {"User-Agent": user_agent}
    out: list[RedditPost] = []

    for sub in subreddits:
        url = f"https://www.reddit.com/r/{sub}/new.json"
        params = {"limit": limit}

        resp = requests.get(url, headers=headers, params=params, timeout=20)

        # If rate-limited or blocked, surface the response code clearly
        if resp.status_code != 200:
            raise RuntimeError(
                f"Reddit JSON fetch failed for r/{sub}: HTTP {resp.status_code}. "
                f"Tip: try later, reduce POST_LIMIT, ensure User-Agent is set."
            )

        payload = resp.json()
        children = payload.get("data", {}).get("children", [])

        for ch in children:
            d = ch.get("data", {})
            post_id = str(d.get("id", ""))
            if not post_id:
                continue

            permalink = d.get("permalink", "")
            full_url = f"https://www.reddit.com{permalink}" if permalink else ""

            out.append(
                RedditPost(
                    external_id=post_id,
                    subreddit=sub,
                    author=str(d.get("author", "") or ""),
                    title=str(d.get("title", "") or ""),
                    body=str(d.get("selftext", "") or ""),
                    score=_safe_int(d.get("score", 0)),
                    num_comments=_safe_int(d.get("num_comments", 0)),
                    url=full_url,
                    created_at=_utc_from_ts(float(d.get("created_utc", 0.0) or 0.0)),
                )
            )

        # be a good citizen
        sleep(1.0)

    return out
