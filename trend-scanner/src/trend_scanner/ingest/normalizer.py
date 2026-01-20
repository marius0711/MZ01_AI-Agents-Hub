from __future__ import annotations

from datetime import datetime
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from trend_scanner.db.models import RawItem
from trend_scanner.ingest.collector import RedditPost


def upsert_posts(session: Session, posts: list[RedditPost]) -> int:
    inserted = 0
    now = datetime.utcnow()

    for p in posts:
        row = RawItem(
            platform="reddit",
            external_id=p.external_id,
            subreddit=p.subreddit,
            author=p.author,
            title=p.title,
            body=p.body,
            score=p.score,
            num_comments=p.num_comments,
            url=p.url,
            created_at=p.created_at,
            pulled_at=now,
        )
        session.add(row)
        try:
            session.commit()
            inserted += 1
        except IntegrityError:
            session.rollback()  # duplicate external_id
    return inserted
