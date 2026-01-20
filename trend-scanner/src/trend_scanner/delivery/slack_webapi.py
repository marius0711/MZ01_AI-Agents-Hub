from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import requests


SLACK_API = "https://slack.com/api"


def _api_post(token: str, method: str, *, json: dict[str, Any] | None = None, data: dict[str, Any] | None = None) -> dict[str, Any]:
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{SLACK_API}/{method}"
    r = requests.post(url, headers=headers, json=json, data=data, timeout=30)
    r.raise_for_status()
    payload = r.json()
    if not payload.get("ok"):
        raise RuntimeError(f"Slack API error in {method}: {payload}")
    return payload


def post_message(token: str, channel_id: str, text: str, *, thread_ts: str | None = None) -> str:
    body: dict[str, Any] = {"channel": channel_id, "text": text}
    if thread_ts:
        # Slack expects thread_ts as string
        body["thread_ts"] = str(thread_ts)
    resp = _api_post(token, "chat.postMessage", json=body)
    return str(resp["ts"])


def upload_file_external(token: str, channel_id: str, file_path: Path, *, title: str, initial_comment: str | None = None) -> dict[str, Any]:
    """
    New upload flow (files.upload is deprecated/sunset for new apps):
    1) files.getUploadURLExternal
    2) POST bytes to upload_url
    3) files.completeUploadExternal
    """
    file_path = Path(file_path)
    size = file_path.stat().st_size
    filename = file_path.name

    # 1) get upload URL
    up = _api_post(
        token,
        "files.getUploadURLExternal",
        data={"filename": filename, "length": str(size)},
    )
    upload_url = up["upload_url"]
    file_id = up["file_id"]

    # 2) upload bytes to returned URL
    with file_path.open("rb") as f:
        r = requests.post(upload_url, files={"file": (filename, f)}, timeout=60)
        r.raise_for_status()

    # 3) complete upload & share in channel
    payload: dict[str, Any] = {
        "files": [{"id": file_id, "title": title}],
        "channel_id": channel_id,
    }
    if initial_comment:
        payload["initial_comment"] = initial_comment

    done = _api_post(token, "files.completeUploadExternal", json=payload)
    return done
