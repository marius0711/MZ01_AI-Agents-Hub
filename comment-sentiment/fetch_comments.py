import json
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from googleapiclient.discovery import build

import config  # read optional settings safely

from config import (
    YOUTUBE_API_KEY,
    CHANNEL_HANDLE,
    MAX_VIDEOS,
    MAX_COMMENTS,
)

OUTPUT_PATH = "data/raw_comments.json"

# ---- Flexible defaults (override via config.py if present) ----
DEFAULT_WEEKS_BACK = 3
COMMENTS_PAGE_SIZE = 100  # commentThreads().list maxResults cap = 100


def _debug(msg: str) -> None:
    print(f"[debug] {msg}")


def _get_config_int(name: str, default: int) -> int:
    """Read optional int from config.py without crashing if missing."""
    try:
        return int(getattr(config, name, default))
    except Exception:
        return default


def youtube_client():
    if not YOUTUBE_API_KEY:
        raise ValueError("YOUTUBE_API_KEY is missing in config.py")
    return build("youtube", "v3", developerKey=YOUTUBE_API_KEY)


def to_rfc3339_z(dt: datetime) -> str:
    """YouTube expects RFC3339 timestamps. Use Z suffix."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def compute_cutoff() -> datetime:
    """
    Prefer WEEKS_BACK=3. If DAYS_BACK exists, respect it (explicit wins).
    """
    weeks_back = _get_config_int("WEEKS_BACK", DEFAULT_WEEKS_BACK)
    days_back = getattr(config, "DAYS_BACK", None)

    if days_back is not None:
        try:
            days_back = int(days_back)
            return datetime.now(timezone.utc) - timedelta(days=days_back)
        except Exception:
            pass

    return datetime.now(timezone.utc) - timedelta(weeks=weeks_back)


def parse_rfc3339(published_at: str) -> Optional[datetime]:
    """Parse YouTube RFC3339 timestamps like '2025-12-16T07:18:38Z'."""
    if not published_at:
        return None
    try:
        return datetime.fromisoformat(published_at.replace("Z", "+00:00"))
    except Exception:
        return None


def get_channel_id(youtube) -> str:
    """
    Deterministic channel id resolution.
    Prefer channels().list(forHandle=...) (exact) if supported.
    Fallback to search only if necessary.
    """
    if not CHANNEL_HANDLE:
        raise ValueError("CHANNEL_HANDLE is missing in config.py")

    handle = CHANNEL_HANDLE.strip()

    # 1) Prefer exact handle resolution
    try:
        resp = youtube.channels().list(
            part="id",
            forHandle=handle.lstrip("@"),
            maxResults=1,
        ).execute()
        items = resp.get("items", [])
        if items and items[0].get("id"):
            channel_id = items[0]["id"]
            _debug(f"resolved via forHandle: channel_id={channel_id}")
            return channel_id
    except Exception as e:
        _debug(f"forHandle not available or failed, falling back to search(): {e}")

    # 2) Fallback: search (less reliable)
    request = youtube.search().list(
        part="snippet",
        q=handle,
        type="channel",
        maxResults=1,
    )
    response = request.execute()
    items = response.get("items", [])
    if not items:
        raise ValueError(f"Could not resolve channel for handle/query: {handle}")

    channel_id = items[0].get("id", {}).get("channelId")
    if not channel_id:
        raise ValueError("Could not read channelId from YouTube search response.")
    _debug(f"resolved via search(): channel_id={channel_id}")
    return channel_id


def get_uploads_playlist_id(youtube, channel_id: str) -> str:
    """
    Deterministic way to get all uploads:
    channels().list(contentDetails) -> relatedPlaylists.uploads
    Includes debug logging of resolved channel title and uploads playlist id.
    """
    resp = youtube.channels().list(
        part="contentDetails,snippet",
        id=channel_id,
    ).execute()

    items = resp.get("items", [])
    if not items:
        raise ValueError("Could not fetch channel contentDetails to resolve uploads playlist.")

    title = items[0].get("snippet", {}).get("title", "n/a")
    uploads = items[0]["contentDetails"]["relatedPlaylists"]["uploads"]
    _debug(f"channel_id={channel_id} title='{title}' uploads_playlist_id={uploads}")
    return uploads


def _chunk(lst: List[str], n: int) -> List[List[str]]:
    return [lst[i:i + n] for i in range(0, len(lst), n)]


def get_recent_videos(
    youtube,
    channel_id: str,
    cutoff_dt: datetime,
) -> List[Dict[str, Any]]:
    """
    Reliable approach:
    - get upload playlist -> collect videoIds (newest first)
    - fetch real video publish dates via videos().list(part=snippet)
    - filter by snippet.publishedAt >= cutoff_dt

    Adds debug counters so you can see where '0 videos' comes from.
    """
    uploads_playlist_id = get_uploads_playlist_id(youtube, channel_id)

    # 1) Collect video IDs from uploads playlist (newest first)
    video_ids: List[str] = []
    next_page: Optional[str] = None

    while True:
        resp = youtube.playlistItems().list(
            part="contentDetails",
            playlistId=uploads_playlist_id,
            maxResults=50,
            pageToken=next_page,
        ).execute()

        items = resp.get("items", [])
        if not items:
            break

        for item in items:
            vid = item.get("contentDetails", {}).get("videoId")
            if vid:
                video_ids.append(vid)
            if len(video_ids) >= MAX_VIDEOS * 5:
                # grab more IDs to survive invalid/private/deleted ones
                break

        if len(video_ids) >= MAX_VIDEOS * 5:
            break

        next_page = resp.get("nextPageToken")
        if not next_page:
            break

    _debug(f"uploads playlist returned video_ids={len(video_ids)} (first 5): {video_ids[:5]}")

    if not video_ids:
        return []

    # 2) Fetch true video metadata in batches
    videos: List[Dict[str, Any]] = []
    kept, too_old, parse_fail, missing_snippet = 0, 0, 0, 0
    api_items_total = 0

    for batch in _chunk(video_ids, 50):
        vresp = youtube.videos().list(
            part="snippet",
            id=",".join(batch),
        ).execute()

        items = vresp.get("items", [])
        api_items_total += len(items)

        for item in items:
            snip = item.get("snippet")
            if not snip:
                missing_snippet += 1
                continue

            published_at = snip.get("publishedAt", "")
            dt = parse_rfc3339(published_at)
            if not dt:
                parse_fail += 1
                continue

            if dt < cutoff_dt:
                too_old += 1
                continue

            videos.append({
                "video_id": item.get("id"),
                "title": snip.get("title", ""),
                "published_at": published_at,
            })
            kept += 1

    _debug(
        f"videos().list returned items={api_items_total}; kept={kept} "
        f"too_old={too_old} parse_fail={parse_fail} missing_snippet={missing_snippet}"
    )

    # 3) Sort newest->oldest and cap MAX_VIDEOS
    videos.sort(key=lambda x: x.get("published_at", ""), reverse=True)
    videos = videos[:MAX_VIDEOS]

    _debug(f"final recent videos={len(videos)}; newest={videos[0]['published_at'] if videos else 'n/a'}")
    return videos


def fetch_comments_for_video(
    youtube,
    video: Dict[str, Any],
    cutoff_dt: Optional[datetime] = None,
) -> List[Dict[str, Any]]:
    """
    Fetch top-level comments.
    If cutoff_dt is provided, discard comments older than cutoff_dt.
    """
    comments: List[Dict[str, Any]] = []
    next_page: Optional[str] = None

    while True:
        request = youtube.commentThreads().list(
            part="snippet",
            videoId=video["video_id"],
            maxResults=COMMENTS_PAGE_SIZE,
            pageToken=next_page,
            textFormat="plainText",
        )
        response = request.execute()

        for item in response.get("items", []):
            snippet = item["snippet"]["topLevelComment"]["snippet"]
            published_at = snippet.get("publishedAt", "")

            if cutoff_dt and published_at:
                dt = parse_rfc3339(published_at)
                if dt and dt < cutoff_dt:
                    continue

            comments.append({
                "video_id": video["video_id"],
                "video_title": video.get("title", ""),
                "comment_id": item["snippet"]["topLevelComment"]["id"],
                "text": snippet.get("textDisplay", ""),
                "author": snippet.get("authorDisplayName"),
                "published_at": published_at,
                "like_count": snippet.get("likeCount", 0),
            })

            if len(comments) >= MAX_COMMENTS:
                return comments

        next_page = response.get("nextPageToken")
        if not next_page:
            break

    return comments


def main():
    os.makedirs("data", exist_ok=True)

    youtube = youtube_client()

    print("Resolving channel ID...")
    channel_id = get_channel_id(youtube)

    cutoff_dt = compute_cutoff()
    cutoff_rfc3339 = to_rfc3339_z(cutoff_dt)

    weeks_back = _get_config_int("WEEKS_BACK", DEFAULT_WEEKS_BACK)
    days_back = getattr(config, "DAYS_BACK", None)
    window_desc = f"{days_back} days" if days_back is not None else f"{weeks_back} weeks"
    print(f"Fetching videos since {cutoff_rfc3339} (window: last {window_desc})...")

    videos = get_recent_videos(youtube, channel_id, cutoff_dt=cutoff_dt)
    print(f"Found {len(videos)} videos")

    all_comments: List[Dict[str, Any]] = []

    for idx, video in enumerate(videos, 1):
        print(f"[{idx}/{len(videos)}] Fetching comments for: {video.get('title','')}")
        comments = fetch_comments_for_video(youtube, video, cutoff_dt=cutoff_dt)
        all_comments.extend(comments)

        if len(all_comments) >= MAX_COMMENTS:
            all_comments = all_comments[:MAX_COMMENTS]
            break

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(all_comments, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(all_comments)} comments to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
