from __future__ import annotations

from datetime import datetime, timedelta, timezone
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from trend_scanner.db.models import RawItem


def _metric_row(r: RawItem) -> int:
    return int(r.score) + int(r.num_comments)


def _compact_title(t: str, max_len: int = 110) -> str:
    t = (t or "").strip().replace("\n", " ")
    return t if len(t) <= max_len else t[: max_len - 1] + "…"


def _flag(r: RawItem) -> str:
    title = (r.title or "").lower()

    if "?" in title or title.startswith(("how ", "why ", "what ", "help", "anyone")):
        return "QUESTION"

    # comment-heavy: more comments than score or high absolute comments
    if r.num_comments >= 80 or r.num_comments >= max(10, r.score):
        return "DISCUSS"

    if _metric_row(r) >= 500:
        return "POP"

    return ""


def render_weekly_md(session: Session, subreddits: list[str], limit: int = 50) -> str:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    since = now - timedelta(days=7)

    engagement_expr = (RawItem.score + RawItem.num_comments)

    stmt = (
        select(RawItem)
        .where(RawItem.subreddit.in_(subreddits))
        .where(RawItem.created_at >= since)
        .order_by(engagement_expr.desc())
        .limit(limit)
    )

    rows = session.execute(stmt).scalars().all()

    # Executive Summary stats
    per_sub = defaultdict(int)
    for r in rows:
        per_sub[r.subreddit] += _metric_row(r)

    top_subs = sorted(per_sub.items(), key=lambda x: x[1], reverse=True)[:5]
    discussion = sorted(rows, key=lambda r: (r.num_comments, _metric_row(r)), reverse=True)[:5]

    now_str = now.strftime("%Y-%m-%d %H:%M UTC")
    since_str = since.strftime("%Y-%m-%d %H:%M UTC")

    lines: list[str] = []
    lines.append("# Reddit Weekly Digest (Compact)\n")
    lines.append(f"- Generated: **{now_str}**")
    lines.append(f"- Range: **last 7 days** (since {since_str})")
    lines.append(f"- Subreddits: **{', '.join(subreddits)}**")
    lines.append(f"- Items shown: **Top {limit}** by engagement (score + comments)\n")

    lines.append("## Executive Summary\n")
    lines.append("**Top subreddits by engagement (from this Top list):**")
    for sub, val in top_subs:
        lines.append(f"- r/{sub}: {val}")
    lines.append("")
    lines.append("**Top discussion drivers (comment-heavy):**")
    for r in discussion:
        lines.append(
            f"- r/{r.subreddit} | comments {r.num_comments}, score {r.score} | {_compact_title(r.title, 90)}"
        )
    lines.append("")

    lines.append("## Top 10 (detailed)\n")
    for i, r in enumerate(rows[:10], start=1):
        flag = _flag(r)
        flag_txt = f" [{flag}]" if flag else ""
        lines.append(f"{i}. **{_compact_title(r.title, 140)}**{flag_txt}")
        lines.append(
            f"   - r/{r.subreddit} | metric {_metric_row(r)} (score {r.score}, comments {r.num_comments})"
        )
        if r.url:
            lines.append(f"   - {r.url}")
        lines.append("")

    if len(rows) > 10:
        lines.append("## 11–50 (compact list)\n")
        for i, r in enumerate(rows[10:], start=11):
            flag = _flag(r)
            flag_txt = f"[{flag}] " if flag else ""
            lines.append(
                f"{i}. {flag_txt}{_compact_title(r.title, 120)} — r/{r.subreddit} | m={_metric_row(r)} (s={r.score}, c={r.num_comments})"
            )
            if r.url:
                lines.append(f"   {r.url}")
        lines.append("")

    return "\n".join(lines)
