from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from rich import print

from trend_scanner.config.settings import Settings
from trend_scanner.db.models import Base
from trend_scanner.db.session import make_engine, make_session_factory
from trend_scanner.delivery.weekly_md import render_weekly_md
from trend_scanner.delivery.pdf_report import markdown_to_simple_pdf
from trend_scanner.delivery.slack_webapi import post_message, upload_file_external
from trend_scanner.delivery.slack import post_weekly_summary
import os


def iso_week_stamp(dt: datetime) -> str:
    y, w, _ = dt.isocalendar()
    return f"{y}-W{w:02d}"


def main() -> None:
    load_dotenv(dotenv_path=Path(".env"))
    s = Settings()

    Path("data").mkdir(parents=True, exist_ok=True)
    Path(s.output_dir).mkdir(parents=True, exist_ok=True)

    engine = make_engine(s.db_url)
    Base.metadata.create_all(engine)
    SessionFactory = make_session_factory(engine)

    subreddits = s.subreddit_list()

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    stamp = iso_week_stamp(now)

    md_path = Path(s.output_dir) / f"weekly_{stamp}.md"
    pdf_path = Path(s.output_dir) / f"weekly_{stamp}.pdf"

    with SessionFactory() as session:
        md = render_weekly_md(session, subreddits=subreddits, limit=50)

    md_path.write_text(md, encoding="utf-8")
    markdown_to_simple_pdf(md, pdf_path)

    print(f"[green]Wrote[/green] {md_path}")
    print(f"[cyan]Wrote[/cyan] {pdf_path}")
    # Slack delivery (optional): file upload + thread summary
    if s.slack_bot_token and s.slack_channel_id:
        # Upload PDF (preview in Slack)
        upload_file_external(
            token=s.slack_bot_token,
            channel_id=s.slack_channel_id,
            file_path=pdf_path,
            title=pdf_path.name,
            initial_comment=None,
        )

        # Post headline message and then reply in thread with highlights
        head_ts = post_message(
            token=s.slack_bot_token,
            channel_id=s.slack_channel_id,
            text=f"📊 Weekly Reddit Trend Digest ({stamp})\n• Subreddits: {', '.join(subreddits)}\n• Top 50 posts (verdichtet, kompakt)\n📎 PDF wurde hochgeladen (Preview im Channel).",
        )

        # Lightweight highlights (no LLM): take first lines from the MD executive summary section
        md_lines = md.splitlines()
        highlights = []
        in_exec = False
        for line in md_lines:
            if line.strip() == "## Executive Summary":
                in_exec = True
                continue
            if in_exec and line.startswith("## "):
                break
            if in_exec and line.strip().startswith("- "):
                highlights.append(line.strip()[2:])
            if len(highlights) >= 6:
                break

        if highlights:
            post_message(
                token=s.slack_bot_token,
                channel_id=s.slack_channel_id,
                thread_ts=head_ts,
                text="*Highlights*\n" + "\n".join([f"• {h}" for h in highlights]),
            )


    webhook = s.slack_webhook_url
    if webhook:
        post_weekly_summary(
            webhook_url=webhook,
            title="📊 Weekly Reddit Trend Digest",
            highlights=[
                f"Subreddits: {', '.join(subreddits)}",
                "Top 50 posts, verdichtet & kompakt",
            ],
            pdf_path=pdf_path,
        )



if __name__ == "__main__":
    main()
