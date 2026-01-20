from __future__ import annotations

import json
from pathlib import Path
import requests


def post_message(webhook_url: str, text: str) -> None:
    payload = {"text": text}
    r = requests.post(webhook_url, data=json.dumps(payload), headers={"Content-Type": "application/json"})
    r.raise_for_status()


def post_weekly_summary(
    webhook_url: str,
    title: str,
    highlights: list[str],
    pdf_path: Path,
) -> None:
    lines = [f"*{title}*"]
    lines.append("")
    for h in highlights:
        lines.append(f"• {h}")
    lines.append("")
    lines.append(f"📎 Report: `{pdf_path.name}`")

    post_message(webhook_url, "\n".join(lines))
