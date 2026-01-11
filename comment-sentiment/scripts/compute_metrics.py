import json
import config
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
from dateutil.parser import isoparse

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

INPUT_PATH = DATA_DIR / "annotated_comments.json"
OUTPUT_PATH = DATA_DIR / "aggregated_metrics.json"

# --- Intent Shift mapping (MVP-stable) ---
INTENT_GROUPS = {
    "praise": "supportive",
    "question": "neutral",
    "discussion": "neutral",
    "constructive_criticism": "critical",
    "aggressive_criticism": "critical",
}

CRITICAL_INTENTS = {"constructive_criticism", "aggressive_criticism"}
DEFAULT_LATEST_WEEKS = 3

def _get_cfg_int(name: str, default: int) -> int:
    try:
        return int(getattr(config, name, default))
    except Exception:
        return default

LATEST_WEEKS = _get_cfg_int("LATEST_WEEKS", DEFAULT_LATEST_WEEKS)


def load_data(path: Path) -> pd.DataFrame:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return pd.DataFrame(data)


def prepare_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    # ✅ FIX: parse published_at properly
    df["published_at"] = df["published_at"].apply(isoparse)

    # ✅ FIX: keep a real time key for sorting/grouping
    df["week_period"] = df["published_at"].dt.to_period("W")
    df["week"] = df["week_period"].astype(str)  # label only

    # Normalize strings
    df["sentiment"] = df["sentiment"].astype(str).str.strip().str.lower()
    df["intent"] = df["intent"].astype(str).str.strip().str.lower()

    # Ensure emotion intensity exists and is numeric
    if "emotion_intensity" not in df.columns:
        df["emotion_intensity"] = 0.0
    df["emotion_intensity"] = pd.to_numeric(df["emotion_intensity"], errors="coerce").fillna(0.0)

    return df


def restrict_to_latest_weeks(df: pd.DataFrame, n_weeks: int) -> pd.DataFrame:
    """
    Keep only the latest N weeks (based on week_period).
    This is the robust way (no string ordering bugs).
    """
    if n_weeks <= 0 or df.empty:
        return df

    weeks_sorted = sorted(df["week_period"].dropna().unique())
    if len(weeks_sorted) <= n_weeks:
        return df

    keep = set(weeks_sorted[-n_weeks:])
    return df[df["week_period"].isin(keep)].copy()


def sentiment_trend(df: pd.DataFrame) -> pd.DataFrame:
    trend = (
        df.groupby(["week_period", "sentiment"])
        .size()
        .reset_index(name="count")
    )
    trend["ratio"] = trend["count"] / trend.groupby("week_period")["count"].transform("sum")

    # ✅ FIX: stable sort + label for plotting/reporting
    trend = trend.sort_values(["week_period", "sentiment"]).reset_index(drop=True)
    trend["week"] = trend["week_period"].astype(str)
    return trend


def intent_distribution(df: pd.DataFrame) -> pd.DataFrame:
    dist = (
        df.groupby(["week_period", "intent"])
        .size()
        .reset_index(name="count")
    )
    dist["ratio"] = dist["count"] / dist.groupby("week_period")["count"].transform("sum")

    # ✅ FIX: stable sort + label
    dist = dist.sort_values(["week_period", "intent"]).reset_index(drop=True)
    dist["week"] = dist["week_period"].astype(str)
    return dist


def intent_shift(df: pd.DataFrame) -> pd.DataFrame:
    temp = df.copy()
    temp["intent_group"] = temp["intent"].map(INTENT_GROUPS).fillna("other")

    grouped = (
        temp.groupby(["week_period", "intent_group"])
        .size()
        .reset_index(name="count")
    )
    grouped["ratio"] = grouped["count"] / grouped.groupby("week_period")["count"].transform("sum")

    # ✅ FIX: stable sort + label
    grouped = grouped.sort_values(["week_period", "intent_group"]).reset_index(drop=True)
    grouped["week"] = grouped["week_period"].astype(str)
    return grouped


def compute_issues(df: pd.DataFrame) -> pd.DataFrame:
    """
    Issue = (primary_topic, sentiment, intent_group)
    Deterministic: 1 comment -> exactly one issue (primary topic only).
    """
    records = []

    for _, row in df.iterrows():
        topics = row.get("key_topics", [])
        if not isinstance(topics, list) or not topics:
            continue

        records.append({
            "week_period": row["week_period"],
            "week": row["week"],
            "topic": topics[0],  # primary topic
            "sentiment": row["sentiment"],
            "intent_group": INTENT_GROUPS.get(row["intent"], "other"),
            "emotion_intensity": row.get("emotion_intensity", 0.0),
            "comment_text": row.get("text", ""),
        })

    issues_df = pd.DataFrame(records)
    if issues_df.empty:
        return pd.DataFrame(columns=["week", "topic", "sentiment", "intent_group", "comment_count", "avg_emotion"])

    aggregated = (
        issues_df
        .groupby(["week_period", "week", "topic", "sentiment", "intent_group"])
        .agg(
            comment_count=("comment_text", "count"),
            avg_emotion=("emotion_intensity", "mean"),
        )
        .reset_index()
    )

    aggregated["avg_emotion"] = aggregated["avg_emotion"].round(2)
    aggregated = aggregated.sort_values(["week_period", "comment_count"], ascending=[True, False]).reset_index(drop=True)
    # keep output compatible: week stays as label; week_period stays as extra key (harmless)
    return aggregated


def trigger_topics(df: pd.DataFrame, top_n: int = 5):
    """
    Trigger topics are derived from CRITICAL intents (not sentiment).
    Each comment can contribute max 1 vote per topic.
    """
    critical = df[df["intent"].isin(CRITICAL_INTENTS)]

    topics: List[str] = []
    for tlist in critical.get("key_topics", []):
        if isinstance(tlist, list) and tlist:
            topics.extend(set(tlist))

    return Counter(topics).most_common(top_n)


def escalation_score(df: pd.DataFrame):
    """
    Escalation = share of aggressive_criticism comments.
    """
    results = []

    for week_period, g in df.groupby("week_period"):
        total = len(g)
        if total == 0:
            continue

        aggressive = g[g["intent"] == "aggressive_criticism"]
        ratio = len(aggressive) / total

        if ratio < 0.15:
            level = "stable"
        elif ratio < 0.30:
            level = "watch"
        else:
            level = "critical"

        results.append({
            "week": str(week_period),
            "week_period": str(week_period),
            "aggressive_ratio": round(ratio, 3),
            "level": level,
            "thresholds": {"stable_lt": 0.15, "watch_lt": 0.30, "critical_ge": 0.30},
        })

    # ✅ FIX: ensure chronological order
    results = sorted(results, key=lambda x: x["week"])
    return results


def criticism_structure_by_week(df: pd.DataFrame, top_n: int = 5):
    """
    Dominance vs escalation separation:
    - structure: focused if one topic dominates critical mentions (dominance > 0.40), else fragmented
    - dominance: max(topic_count) / total_topic_mentions within critical intents
    """
    results = []

    critical = df[df["intent"].isin(CRITICAL_INTENTS)]
    for week_period, g in critical.groupby("week_period"):
        topics: List[str] = []
        for tlist in g.get("key_topics", []):
            if isinstance(tlist, list) and tlist:
                topics.extend(set(tlist))  # 1 vote per topic per comment

        counts = Counter(topics)
        total_mentions = sum(counts.values())

        if total_mentions == 0:
            results.append({
                "week": str(week_period),
                "week_period": str(week_period),
                "structure": "none",
                "dominance": 0.0,
                "top_topics": [],
                "threshold_focused_gt": 0.40,
            })
            continue

        dominance = max(counts.values()) / total_mentions
        structure = "focused" if dominance > 0.40 else "fragmented"

        results.append({
            "week": str(week_period),
            "week_period": str(week_period),
            "structure": structure,
            "dominance": round(dominance, 3),
            "threshold_focused_gt": 0.40,
            "top_topics": counts.most_common(top_n),
        })

    results = sorted(results, key=lambda x: x["week"])
    return results


def emotion_context_by_week(df: pd.DataFrame):
    """
    Adds baseline comparison:
    - avg_emotion_total
    - avg_emotion_negative
    - lift = neg - total
    - label based on lift thresholds
    """
    results = []

    for week_period, g in df.groupby("week_period"):
        if len(g) == 0:
            continue

        total_avg = float(g["emotion_intensity"].mean())
        neg = g[g["sentiment"] == "negative"]
        neg_avg = float(neg["emotion_intensity"].mean()) if len(neg) else 0.0

        lift = neg_avg - total_avg

        if lift < 0.05:
            label = "normal"
        elif lift < 0.15:
            label = "elevated"
        else:
            label = "high"

        results.append({
            "week": str(week_period),
            "week_period": str(week_period),
            "avg_emotion_total": round(total_avg, 2),
            "avg_emotion_negative": round(neg_avg, 2),
            "emotion_lift": round(lift, 2),
            "emotion_label": label,
            "thresholds": {"normal_lt": 0.05, "elevated_lt": 0.15, "high_ge": 0.15},
        })

    results = sorted(results, key=lambda x: x["week"])
    return results


def trend_flags(sentiment_df: pd.DataFrame, intent_shift_df: pd.DataFrame):
    """
    Uses week_period for ordering (fixes KW order).
    Produces per-week change flags vs previous week:
    - negative_trend (rising/flat/falling)
    - critical_intent_trend (rising/flat/falling)
    """
    weeks = sorted(sentiment_df["week_period"].unique())
    if len(weeks) < 2:
        return []

    def ratio_sent(wp, sent: str) -> float:
        r = sentiment_df[(sentiment_df.week_period == wp) & (sentiment_df.sentiment == sent)]["ratio"]
        return float(r.iloc[0]) if len(r) else 0.0

    def ratio_intent(wp, grp: str) -> float:
        r = intent_shift_df[(intent_shift_df.week_period == wp) & (intent_shift_df.intent_group == grp)]["ratio"]
        return float(r.iloc[0]) if len(r) else 0.0

    def label(delta: float) -> str:
        if delta > 0.05:
            return "rising"
        if delta < -0.05:
            return "falling"
        return "flat"

    flags = []
    for i in range(1, len(weeks)):
        w_prev, w_cur = weeks[i - 1], weeks[i]
        neg_change = ratio_sent(w_cur, "negative") - ratio_sent(w_prev, "negative")
        crit_change = ratio_intent(w_cur, "critical") - ratio_intent(w_prev, "critical")

        flags.append({
            "week": str(w_cur),
            "week_period": str(w_cur),
            "negative_trend": label(neg_change),
            "negative_change": round(neg_change, 3),
            "critical_intent_trend": label(crit_change),
            "critical_intent_change": round(crit_change, 3),
            "threshold_flat_pp": 0.05,
        })

    return flags


def df_json_safe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "week_period" in df.columns:
        df["week_period"] = df["week_period"].astype(str)
    return df

def main():
    df = prepare_dataframe(load_data(INPUT_PATH))
    df = restrict_to_latest_weeks(df, LATEST_WEEKS)

    sentiment_df = sentiment_trend(df)
    intent_dist_df = intent_distribution(df)
    intent_shift_df = intent_shift(df)

    issues_df = compute_issues(df)

    output: Dict[str, Any] = {
        "sentiment_trend": df_json_safe(sentiment_df).to_dict(orient="records"),
        "intent_distribution": df_json_safe(intent_dist_df).to_dict(orient="records"),
        "intent_shift": df_json_safe(intent_shift_df).to_dict(orient="records"),

        "top_trigger_topics": trigger_topics(df),
        "issues": df_json_safe(issues_df).to_dict(orient="records"),

        "escalation": escalation_score(df),
        "criticism_structure": criticism_structure_by_week(df),
        "emotion_context": emotion_context_by_week(df),
        "trend_flags": trend_flags(sentiment_df, intent_shift_df),
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"[config] LATEST_WEEKS={LATEST_WEEKS}")
    print(f"Metrics written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
