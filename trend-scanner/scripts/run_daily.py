from pathlib import Path

from dotenv import load_dotenv
from rich import print

from trend_scanner.config.settings import Settings
from trend_scanner.db.models import Base
from trend_scanner.db.session import make_engine, make_session_factory
from trend_scanner.ingest.collector import fetch_new_posts
from trend_scanner.ingest.normalizer import upsert_posts
from trend_scanner.delivery.digest_md import render_digest_md


def main() -> None:
    load_dotenv(dotenv_path=Path(".env"))
    s = Settings()

    Path("data").mkdir(parents=True, exist_ok=True)
    Path(s.output_dir).mkdir(parents=True, exist_ok=True)

    engine = make_engine(s.db_url)
    Base.metadata.create_all(engine)
    SessionFactory = make_session_factory(engine)

    subreddits = s.subreddit_list()
    print(f"[bold]Fetching[/bold] {s.post_limit} new posts per subreddit: {subreddits}")

    posts = fetch_new_posts(
        user_agent=s.reddit_user_agent,
        subreddits=subreddits,
        limit=s.post_limit,
    )

    with SessionFactory() as session:
        inserted = upsert_posts(session, posts)
        print(f"[green]Inserted[/green] {inserted} new posts (deduped).")
        md = render_digest_md(session, subreddits=subreddits, limit=30)

    out_path = Path(s.output_dir) / "digest.md"
    out_path.write_text(md, encoding="utf-8")
    print(f"[bold cyan]Wrote[/bold cyan] {out_path}")


if __name__ == "__main__":
    main()
