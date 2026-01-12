import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import config


# -----------------------------
# Helpers
# -----------------------------
def slugify_channel(handle: str) -> str:
    """'@timgabelofficial' -> 'timgabelofficial' (fallback: 'channel')."""
    s = (handle or "").strip()
    if s.startswith("@"):
        s = s[1:]
    s = s.lower()
    s = "".join(ch for ch in s if ch.isalnum() or ch in ("-", "_"))
    return s or "channel"


def get_cfg_int(name: str, default: int) -> int:
    """Read int from config with safe fallback."""
    try:
        return int(getattr(config, name, default))
    except Exception:
        return default


def index_by_week(records: Iterable[Dict[str, Any]], week_key: str = "week") -> Dict[str, Dict[str, Any]]:
    """list[dict] -> dict[week] = record"""
    idx: Dict[str, Dict[str, Any]] = {}
    for r in records or []:
        w = r.get(week_key)
        if w:
            idx[str(w)] = r
    return idx


def sorted_weeks(records: Iterable[Dict[str, Any]]) -> List[str]:
    weeks: List[str] = []
    for r in records or []:
        w = r.get("week")
        if w:
            weeks.append(str(w))
    return sorted(set(weeks))


def safe_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return default
    
def legend_block(escalation_scale_text: str) -> str:
    return (
        "## Skalen & Begriffe (Kurzlegende)\n\n"
        "- **Aggressive Kritik (%):** Anteil von Kommentaren mit stark negativem oder eskalierendem Sprachmuster.\n"
        f"- **Eskalations-Level:** Regelbasierte Einordnung auf Basis des Anteils aggressiver Kritik "
        f"(Skala: {escalation_scale_text}).\n"
        "- **Emotion (0–1):** Modellbasierter Emotionsscore (0 = neutral, 1 = stark emotional).\n"
        "- **Ø negativ:** Durchschnittlicher Emotionswert ausschließlich negativer Kommentare.\n"
        "- **Emotion Lift:** Differenz zwischen Gesamt- und Negativemotion "
        "(höhere Werte = stärkere emotionale Aufladung).\n"
        "- **Kritik-Struktur:** *focused* = ein dominantes Thema; "
        "*fragmented* = mehrere gleichgewichtige Themen.\n"
        "- **Dominanz (0–1):** Anteil des größten Kritik-Themas an allen kritischen Kommentaren "
        "(focused > 0.40).\n"
        "- **Trend (up / flat / down):** Veränderung ggü. Vorwoche relativ zu einer internen Signifikanzschwelle.\n"
    )


def safe_int(v: Any, default: int = 0) -> int:
    try:
        return int(v)
    except Exception:
        return default


def format_top_topics(top_topics: Optional[List[List[Any]]]) -> str:
    """
    top_topics expected like: [[topic, count], ...]
    Produces a markdown bullet list.
    """
    if not top_topics:
        return "Keine dominanten Kritik-Themen in dieser Woche."
    lines: List[str] = []
    for topic, count in top_topics:
        topic = str(topic or "")
        pretty = topic.replace("_", " ")
        lines.append(f"- **{pretty}** (`{topic}`) ({safe_int(count)})")
    return "\n".join(lines)


# -----------------------------
# Domain logic
# -----------------------------
@dataclass(frozen=True)
class Classification:
    status: str
    action: str
    reason: str


def classify_status_for_week(escalation_level: str, criticism_structure: str) -> Classification:
    """
    Deterministic status derivation:
    - escalation_level dominates
    - focused criticism upgrades stable -> watch
    """
    escalation_level = (escalation_level or "").lower()
    criticism_structure = (criticism_structure or "").lower()

    if escalation_level == "critical":
        return Classification(
            status="kritisch",
            action="Aktiv reagieren",
            reason="Hoher Anteil aggressiver Kritik (Eskalations-Level: critical).",
        )
    if escalation_level == "watch":
        return Classification(
            status="beobachtenswert",
            action="Beobachten und ggf. einordnen",
            reason="Erhöhter Anteil aggressiver Kritik (Eskalations-Level: watch).",
        )
    if criticism_structure == "focused":
        return Classification(
            status="beobachtenswert",
            action="Beobachten",
            reason="Kritik ist fokussiert auf ein dominantes Thema, aber ohne Eskalation.",
        )

    return Classification(
        status="stabil",
        action="Kein Handlungsbedarf",
        reason="Keine auffällige Eskalation und keine thematische Verdichtung.",
    )


def pick_focus_week(metrics: Dict[str, Any], weeks_for_range: List[str], min_comments: int = 50) -> str:
    """
    Pick a focus week that is recent AND has enough volume.
    Uses sentiment_trend counts (most reliable aggregate).
    """
    if not weeks_for_range:
        raise ValueError("weeks_for_range is empty.")

    totals: Dict[str, int] = {}
    for r in metrics.get("sentiment_trend", []) or []:
        w = r.get("week")
        c = r.get("count", 0)
        if w:
            totals[str(w)] = totals.get(str(w), 0) + safe_int(c)

    # 1) newest week in range with >= min_comments
    for w in reversed(weeks_for_range):
        if totals.get(w, 0) >= min_comments:
            return w

    # 2) fallback: pick max-volume week within range (if we have totals at all)
    if totals:
        candidates = {w: totals.get(w, 0) for w in weeks_for_range}
        return max(candidates, key=candidates.get)

    # 3) ultimate fallback: newest week
    return weeks_for_range[-1]


# -----------------------------
# IO / Paths
# -----------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CHANNEL_HANDLE = getattr(config, "CHANNEL_HANDLE", "")  # e.g. "@timgabelofficial"
CHANNEL_SLUG = slugify_channel(CHANNEL_HANDLE)

INPUT_PATH = DATA_DIR / f"aggregated_metrics_{CHANNEL_SLUG}.json"
OUTPUT_PATH = OUTPUT_DIR / f"report_{CHANNEL_SLUG}_{date.today().isoformat()}.md"


def load_metrics(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


# -----------------------------
# Report builder
# -----------------------------
def build_report(metrics: Dict[str, Any]) -> str:
    escalation_list = metrics.get("escalation", []) or []
    if not escalation_list:
        raise ValueError(f"No 'escalation' found in {INPUT_PATH.name} (expected new schema).")

    all_weeks = sorted_weeks(escalation_list)
    if not all_weeks:
        raise ValueError("No weeks found in 'escalation' records.")

    latest_weeks_cfg = get_cfg_int("LATEST_WEEKS", 3)
    weeks_for_range = all_weeks[-latest_weeks_cfg:] if latest_weeks_cfg > 0 else all_weeks
    range_start, range_end = weeks_for_range[0], weeks_for_range[-1]

    min_focus_week_comments = get_cfg_int("MIN_FOCUS_WEEK_COMMENTS", 50)
    focus_week = pick_focus_week(metrics, weeks_for_range, min_comments=min_focus_week_comments)

    escalation_by_week = index_by_week(escalation_list)
    latest_esc = escalation_by_week.get(focus_week, {}) or {}

    # Optional blocks
    cs_idx = index_by_week(metrics.get("criticism_structure", []) or [])
    ec_idx = index_by_week(metrics.get("emotion_context", []) or [])
    tf_idx = index_by_week(metrics.get("trend_flags", []) or [])

    cs = cs_idx.get(focus_week, {}) or {}
    ec = ec_idx.get(focus_week, {}) or {}
    tf = tf_idx.get(focus_week, {}) or {}

    # Issues for this week
    issues = metrics.get("issues", []) or []
    issues_week = [i for i in issues if str(i.get("week")) == focus_week]

    critical_issues = sorted(
        (i for i in issues_week if i.get("intent_group") == "critical"),
        key=lambda x: safe_int(x.get("comment_count", 0)),
        reverse=True,
    )[:5]

    supportive_issues = sorted(
        (i for i in issues_week if i.get("intent_group") == "supportive"),
        key=lambda x: safe_int(x.get("comment_count", 0)),
        reverse=True,
    )[:5]

    classification = classify_status_for_week(
        escalation_level=str(latest_esc.get("level", "")),
        criticism_structure=str(cs.get("structure", "")),
    )

    escalation_scale_text = "stable < 15%, watch < 30%, critical ≥ 30%"
    aggressive_ratio_pct = safe_float(latest_esc.get("aggressive_ratio", 0.0)) * 100.0

    # Trend sentence (optional)
    trend_sentence: Optional[str] = None
    if tf:
        trend_sentence = (
            "Trend-Signal (ggü. Vorwoche): "
            f"Negative-Stimmung **{tf.get('negative_trend','n/a')}** (Δ {tf.get('negative_change','n/a')}); "
            f"Kritik-Intent **{tf.get('critical_intent_trend','n/a')}** (Δ {tf.get('critical_intent_change','n/a')})."
        )

    # Emotion context (optional)
    emotion_sentence: Optional[str] = None
    if ec:
        label = ec.get("emotion_label", "n/a")
        emotion_sentence = (
            "Emotionskontext: "
            f"Ø Emotion gesamt **{ec.get('avg_emotion_total','n/a')}**, "
            f"Ø negativ **{ec.get('avg_emotion_negative','n/a')}** "
            f"(Lift {ec.get('emotion_lift','n/a')}, Label: **{label}**)."
        )

    # Dominance/structure (optional)
    dominance_sentence: Optional[str] = None
    if cs.get("structure"):
        dominance_sentence = (
            f"Kritik-Struktur: **{cs.get('structure')}** "
            f"(Dominanz {safe_float(cs.get('dominance', 0.0)):.2f}; Schwelle focused > 0.40)."
        )

    channel_title = CHANNEL_HANDLE or CHANNEL_SLUG

    lines: List[str] = []
    lines.append(f"# Community Sentiment Report – {channel_title}\n")

    # Kurzfazit
    lines.append("## Kurzfazit\n")
    lines.append(f"- **Bewertung:** {classification.status}")
    lines.append(f"- **Empfehlung:** {classification.action}")
    lines.append(f"- **Begründung:** {classification.reason}\n")

    # Datengrundlage & Herleitung
    lines.append("## Datengrundlage & Herleitung\n")
    lines.append(
        f"- **Analysezeitraum:** **{range_start}** bis **{range_end}** "
        f"(Fokus-Woche: **{focus_week}**, Mindestvolumen: {min_focus_week_comments}, LATEST_WEEKS={latest_weeks_cfg})"
    )
    lines.append(
        f"- **Aggressive Kritik (Fokus-Woche):** **{aggressive_ratio_pct:.1f}%** "
        f"(Skala: {escalation_scale_text}; Level: **{latest_esc.get('level','n/a')}**)"
    )
    lines.append(f"- {dominance_sentence}" if dominance_sentence else "- Kritik-Struktur: **n/a**")
    lines.append(f"- {emotion_sentence}" if emotion_sentence else "- Emotionskontext: **n/a**")

    lines.append("")
    lines.append(trend_sentence if trend_sentence else "Trend-Signal: **n/a** (trend_flags fehlen oder nur 1 Woche im Datensatz).")
    lines.append("")

    # Legende
    lines.append(legend_block(escalation_scale_text))
    lines.append("")
    lines.append("") 

    # Visuals
    lines.append("## Sentiment-Entwicklung\n")
    lines.append(f"![](sentiment_trend_{CHANNEL_SLUG}.png)\n")

    lines.append("## Intent-Entwicklung\n")
    lines.append(f"![](intent_shift_{CHANNEL_SLUG}.png)\n")

    # Kritik- & Trigger-Themen
    lines.append("## Kritik- & Trigger-Themen\n")
    top_topics = cs.get("top_topics") if cs else None

    if not top_topics:
        lines.append("Keine klaren Kritik-Cluster in dieser Fokus-Woche (zu wenige kritische Kommentare oder keine Topics).")
        lines.append("")  # Leerzeile nach Hinweis
    else:
        lines.append(format_top_topics(top_topics))
        lines.append("")  # Leerzeile nach der Liste

        if cs.get("structure") == "focused":
            lines.append("**Einordnung (regelbasiert):** Kritik ist fokussiert → beobachten.")
        elif cs.get("structure") == "fragmented":
            lines.append("**Einordnung (regelbasiert):** Kritik ist fragmentiert → kein einzelner Trigger dominiert.")

        lines.append("")  # Leerzeile nach Einordnung


    # Issues
    lines.append("## Top Issues (Fokus-Woche)\n")
    if not issues_week:
        lines.append("Keine Issues verfügbar (fehlende key_topics oder leerer Zeitraum).\n")
    else:
        if supportive_issues:
            lines.append("**Supportive (Support/Lob):**")
            lines.append("")  # wichtig: Liste startet nach Leerzeile
            for i in supportive_issues:
                lines.append(f"- **{i.get('topic')}**: {safe_int(i.get('comment_count'))} (Ø Emotion {i.get('avg_emotion')})")
            lines.append("")

        if critical_issues:
            lines.append("**Kritisch (Constructive/Aggressive):**")
            lines.append("")  # wichtig: Liste startet nach Leerzeile
            for i in critical_issues:
                lines.append(f"- **{i.get('topic')}**: {safe_int(i.get('comment_count'))} (Ø Emotion {i.get('avg_emotion')})")
            lines.append("")

        else:
            lines.append("Keine signifikanten kritischen Issues in dieser Fokus-Woche.\n")

    # Abschluss
    lines.append("## Interpretation & Empfehlung\n")
    lines.append(
        f"Status **{classification.status}** (Fokus-Woche **{focus_week}**), weil:\n"
        f"- Eskalation-Level = **{latest_esc.get('level','n/a')}** (aggressive Kritik {aggressive_ratio_pct:.1f}%)\n"
        f"- Kritik-Struktur = **{cs.get('structure','n/a')}**\n"
        f"- Trend-Signale = **{tf.get('negative_trend','n/a')}** (Sentiment), **{tf.get('critical_intent_trend','n/a')}** (Intent)\n"
        f"\n**Empfehlung:** {classification.action}\n"
    )

    return "\n".join(lines)


def main() -> None:
    metrics = load_metrics(INPUT_PATH)
    report_md = build_report(metrics)

    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        f.write(report_md)

    print(f"Report written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
