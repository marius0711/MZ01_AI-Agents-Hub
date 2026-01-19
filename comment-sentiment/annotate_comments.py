import json
import time
import config
from datetime import datetime
from typing import List, Dict, Any, Optional
from tqdm import tqdm
from anthropic import Anthropic
from pathlib import Path

CLAUDE_API_KEY = getattr(config, "CLAUDE_API_KEY", "")
CLAUDE_MODEL = getattr(config, "CLAUDE_MODEL", "")
BATCH_SIZE = int(getattr(config, "BATCH_SIZE", 10))

def _slugify_channel(handle: str) -> str:
    s = (handle or "").strip()
    if s.startswith("@"):
        s = s[1:]
    s = s.lower()
    s = "".join(ch for ch in s if ch.isalnum() or ch in ("-", "_"))
    return s or "channel"

CHANNEL_HANDLE = getattr(config, "CHANNEL_HANDLE", "")
CHANNEL_SLUG = _slugify_channel(CHANNEL_HANDLE)

# Base directory = comment-sentiment/
ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)


INPUT_PATH = DATA_DIR / f"raw_comments_{CHANNEL_SLUG}.json"
OUTPUT_PATH = DATA_DIR / f"annotated_comments_{CHANNEL_SLUG}.json"  

DEBUG_DIR = DATA_DIR / "debug_claude"
DEBUG_DIR.mkdir(exist_ok=True)

# ---- Flexible defaults (override via config.py if present) ----
DEFAULT_MAX_TOKENS = 3500
DEFAULT_MAX_RETRIES = 2
DEFAULT_SLEEP_SECONDS = 0.5
DEFAULT_REPAIR_ENABLED = True


def _get_cfg(name: str, default):
    return getattr(config, name, default)


MAX_TOKENS = int(_get_cfg("CLAUDE_MAX_TOKENS", DEFAULT_MAX_TOKENS))
MAX_RETRIES = int(_get_cfg("MAX_RETRIES", DEFAULT_MAX_RETRIES))
SLEEP_SECONDS = float(_get_cfg("SLEEP_SECONDS", DEFAULT_SLEEP_SECONDS))
REPAIR_ENABLED = bool(_get_cfg("REPAIR_JSON_ENABLED", DEFAULT_REPAIR_ENABLED))


SYSTEM_PROMPT = """
You are an analytical assistant for community feedback analysis.

Classify each YouTube comment objectively and conservatively.
Do not infer intent beyond what is clearly expressed.
When uncertain, prefer neutral sentiment and "discussion" or "other" intent.
Do not explain your reasoning.

Output format rules:
- Return ONLY a valid JSON array (no markdown, no extra text).
- Each element must be an object with: id, sentiment, intent, emotion_intensity, key_topics.

Sentiment:
- positive | neutral | negative

Intent:
- praise | question | constructive_criticism | aggressive_criticism | discussion | other
Definitions:
- aggressive_criticism = insults, personal attacks, contempt, demeaning language
- constructive_criticism = criticism with reasons or suggestions; not attacking the person

Emotion intensity (0.0 to 1.0):
- 0.0 = purely informational / no emotion
- 0.3 = mild emotion
- 0.6 = strong emotion
- 0.9 = rage/insults

Topics:
- Provide 0 to 3 topics, snake_case, reusable, abstract.
- Avoid generic topics like "this_video", "creator", "content".
- Avoid names and specific events.
"""


def build_user_prompt(comments: List[Dict[str, Any]]) -> str:
    payload = [{"id": c["comment_id"], "text": c.get("text", "")} for c in comments]
    return f"""
Analyze the following YouTube comments.

For each comment, return an object with:
- id (same as input)
- sentiment: positive | neutral | negative
- intent: praise | question | constructive_criticism | aggressive_criticism | discussion | other
- emotion_intensity: float between 0.0 and 1.0
- key_topics: up to 3 abstract, reusable topics (snake_case)

Comments:
{json.dumps(payload, ensure_ascii=False, indent=2)}
"""


def _debug_dump(prefix: str, text: str) -> str:
    ts = int(time.time())
    path = DEBUG_DIR / f"{prefix}_{ts}.txt"
    path.write_text(text, encoding="utf-8")
    return str(path)


def _strip_code_fences(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[-1]
        if t.endswith("```"):
            t = t.rsplit("```", 1)[0]
    return t.strip()


def _extract_json_array(text: str) -> str:
    """
    Try to extract the first JSON array from a response.
    Handles cases where the model adds extra text before/after.
    """
    t = _strip_code_fences(text)
    start = t.find("[")
    end = t.rfind("]")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON array found in Claude response.")
    return t[start:end + 1]


def _safe_parse_claude_json(raw_text: str) -> List[Dict[str, Any]]:
    json_text = _extract_json_array(raw_text)
    data = json.loads(json_text)
    if not isinstance(data, list):
        raise ValueError("Claude response JSON is not a list.")
    return data


def repair_json_with_claude(client: Anthropic, raw_text: str) -> List[Dict[str, Any]]:
    """
    Second-pass deterministic "format repair" only.
    We do not change semantics; we only enforce valid JSON.
    """
    repair_prompt = f"""
You will be given text that is intended to be a JSON array but contains JSON syntax errors.

Task:
- Fix ONLY the syntax so it becomes valid JSON.
- Do NOT change any values/labels/content except what is strictly required for valid JSON.
- Return ONLY the corrected JSON array (no markdown, no extra text).

Broken JSON:
{raw_text}
"""
    msg = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=MAX_TOKENS,
        temperature=0,
        system="You fix JSON formatting. Output only valid JSON.",
        messages=[{"role": "user", "content": repair_prompt}],
    )
    fixed = msg.content[0].text.strip()
    return _safe_parse_claude_json(fixed)


def annotate_batch(client: Anthropic, batch: List[Dict[str, Any]], attempt: int = 1) -> List[Dict[str, Any]]:
    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=MAX_TOKENS,
        temperature=0,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": build_user_prompt(batch)}],
    )
    raw_text = message.content[0].text.strip()

    try:
        return _safe_parse_claude_json(raw_text)
    except Exception as e:
        bad_path = _debug_dump(f"claude_bad_json_attempt{attempt}", raw_text)

        # Optional repair pass (highly effective in practice)
        if REPAIR_ENABLED:
            try:
                repaired = repair_json_with_claude(client, raw_text)
                return repaired
            except Exception as repair_err:
                rep_path = _debug_dump(f"claude_repair_failed_attempt{attempt}", str(repair_err))
                raise ValueError(
                    f"Claude returned invalid JSON (dumped to {bad_path}). "
                    f"Repair also failed (dumped to {rep_path}). "
                    f"Original error: {e}"
                ) from repair_err

        raise ValueError(f"Claude did not return valid JSON (dumped to {bad_path}). Original error: {e}") from e


def _load_json(path: Path, default):
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default
    except json.JSONDecodeError as e:
        backup = path.with_suffix(
            f".corrupt_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        path.rename(backup)
        print(f"[warn] JSON decode failed for {path}. Moved to {backup}. Starting fresh.")
        return default


def _collect_annotated_ids(annotated: List[Dict[str, Any]]) -> set:
    """
    Robust resume:
    Prefer comment_id, fallback to id (older schema).
    """
    ids = set()
    for a in annotated:
        if isinstance(a, dict):
            if a.get("comment_id"):
                ids.add(a["comment_id"])
            elif a.get("id") and isinstance(a["id"], str):
                ids.add(a["id"])
    return ids


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def _normalize_topic(t: str) -> str:
    t = t.strip().lower().replace(" ", "_").replace("-", "_")
    # keep simple snake_case-ish
    t = "".join(ch for ch in t if ch.isalnum() or ch == "_")
    while "__" in t:
        t = t.replace("__", "_")
    return t.strip("_")


def _normalize_annotation_fields(ann: Dict[str, Any]) -> Dict[str, Any]:
    allowed_sent = {"positive", "neutral", "negative"}
    allowed_intent = {"praise", "question", "constructive_criticism", "aggressive_criticism", "discussion", "other"}

    sent = str(ann.get("sentiment", "neutral")).strip().lower()
    intent = str(ann.get("intent", "other")).strip().lower()

    emo = ann.get("emotion_intensity", 0.0)
    try:
        emo = float(emo)
    except Exception:
        emo = 0.0
    emo = _clamp(emo, 0.0, 1.0)

    topics = ann.get("key_topics", [])
    if not isinstance(topics, list):
        topics = []

    norm_topics: List[str] = []
    for t in topics:
        if isinstance(t, (str, int, float)):
            s = _normalize_topic(str(t))
            if s:
                norm_topics.append(s)

    # unique, preserve order, max 3
    seen = set()
    deduped = []
    for t in norm_topics:
        if t not in seen:
            seen.add(t)
            deduped.append(t)
    deduped = deduped[:3]

    return {
        "sentiment": sent if sent in allowed_sent else "neutral",
        "intent": intent if intent in allowed_intent else "other",
        "emotion_intensity": emo,
        "key_topics": deduped,
    }


def main():
    comments: List[Dict[str, Any]] = _load_json(INPUT_PATH, default=[])
    if not comments:
        print("No raw comments found. Aborting.")
        return

    annotated: List[Dict[str, Any]] = _load_json(OUTPUT_PATH, default=[])
    annotated_ids = _collect_annotated_ids(annotated)

    # Optional test mode via config
    TEST_LIMIT: Optional[int] = getattr(config, "TEST_LIMIT", None)
    if TEST_LIMIT is not None:
        comments = comments[:TEST_LIMIT]

    remaining = [c for c in comments if c.get("comment_id") and c.get("comment_id") not in annotated_ids]

    print(f"Total raw comments (after TEST_LIMIT): {len(comments)}")
    print(f"Annotated file rows: {len(annotated)}")
    print(f"Recognized annotated_ids: {len(annotated_ids)}")
    print(f"Remaining to annotate: {len(remaining)}")
    print(f"[config] BATCH_SIZE={BATCH_SIZE} MAX_TOKENS={MAX_TOKENS} MAX_RETRIES={MAX_RETRIES} REPAIR={REPAIR_ENABLED}")

    if not remaining:
        print("Nothing left to annotate.")
        return

    if not CLAUDE_MODEL:
        raise ValueError("CLAUDE_MODEL missing in config.py")
    client = Anthropic(api_key=CLAUDE_API_KEY)

    for i in tqdm(range(0, len(remaining), BATCH_SIZE)):
        batch = remaining[i:i + BATCH_SIZE]
        batch_by_id = {c["comment_id"]: c for c in batch if "comment_id" in c}

        annotations: Optional[List[Dict[str, Any]]] = None
        for attempt in range(1, MAX_RETRIES + 2):
            try:
                annotations = annotate_batch(client, batch, attempt=attempt)
                break
            except Exception as e:
                print(f"Error in batch starting at index {i} (attempt {attempt}): {e}")
                time.sleep(2 * attempt)

        if annotations is None:
            # Skip batch if all retries fail
            continue

        # Merge deterministically by id
        for ann in annotations:
            cid = ann.get("id")
            if cid not in batch_by_id:
                continue

            original = batch_by_id[cid]
            norm = _normalize_annotation_fields(ann)

            annotated.append({**original, **norm})
            annotated_ids.add(cid)

        # Crash-safe write after each batch
        with OUTPUT_PATH.open("w", encoding="utf-8") as f:
            json.dump(annotated, f, ensure_ascii=False, indent=2)


        time.sleep(SLEEP_SECONDS)

    print(f"Annotated {len(annotated)} comments → {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
