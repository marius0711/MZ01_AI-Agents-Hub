from __future__ import annotations

from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import Session

from trend_scanner.db.models import RawItem


def render_digest_md(session: Session, subreddits: list[str], limit: int = 30) -> str:
    stmt = (
        select(RawItem)
        .where(RawItem.subreddit.in_(subreddits))
        .order_by((RawItem.score + RawItem.num_comments).desc())
        .limit(limit)
    )
    rows = session.execute(stmt).scalars().all()

    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    lines: list[str] = []
    lines.append("# Reddit Trend Digest (MVP)\n")
    lines.append(f"- Generated: **{now}**")
    lines.append(f"- Subreddits: **{', '.join(subreddits)}**\n")

    lines.append("## Top posts (score + comments)\n")

    for i, r in enumerate(rows, start=1):
        metric = r.score + r.num_comments
        title = (r.title or "").strip().replace("\n", " ")
        lines.append(f"{i}. **{title}**")
        lines.append(
            f"   - r/{r.subreddit} | metric: {metric} (score {r.score}, comments {r.num_comments})"
        )
        if r.url:
            lines.append(f"   - {r.url}")
        if r.body:
            snippet = r.body.strip().replace("\n", " ")
            if len(snippet) > 220:
                snippet = snippet[:220] + "…"
            lines.append(f"   - {snippet}")
        lines.append("")

    return "\n".join(lines)
