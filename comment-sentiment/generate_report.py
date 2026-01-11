import json
import config
from datetime import date
from pathlib import Path

# --- paths ---
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

INPUT_PATH = DATA_DIR / "aggregated_metrics.json"
OUTPUT_PATH = OUTPUT_DIR / f"report_biasedskeptic_{date.today()}.md"


def load_metrics():
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _index_by_week(records, week_key="week"):
    """list[dict] -> dict[week] = dict(record)"""
    idx = {}
    for r in records or []:
        w = r.get(week_key)
        if w:
            idx[w] = r
    return idx


def _sorted_weeks_from_records(records):
    weeks = []
    for r in records or []:
        w = r.get("week")
        if w:
            weeks.append(w)
    return sorted(set(weeks))


def _get_cfg_int(name: str, default: int) -> int:
    try:
        return int(getattr(config, name, default))
    except Exception:
        return default


def classify_status_for_week(escalation_level: str, criticism_structure: str):
    """
    Deterministic status derivation:
    - escalation_level dominates
    - focused criticism upgrades stable -> watch
    """
    escalation_level = (escalation_level or "").lower()
    criticism_structure = (criticism_structure or "").lower()

    if escalation_level == "critical":
        return {
            "status": "kritisch",
            "action": "Aktiv reagieren",
            "reason": "Hoher Anteil aggressiver Kritik (Eskalations-Level: critical)."
        }
    if escalation_level == "watch":
        return {
            "status": "beobachtenswert",
            "action": "Beobachten und ggf. einordnen",
            "reason": "Erhöhter Anteil aggressiver Kritik (Eskalations-Level: watch)."
        }

    if criticism_structure == "focused":
        return {
            "status": "beobachtenswert",
            "action": "Beobachten",
            "reason": "Kritik ist fokussiert auf ein dominantes Thema, aber ohne Eskalation."
        }

    return {
        "status": "stabil",
        "action": "Kein Handlungsbedarf",
        "reason": "Keine auffällige Eskalation und keine thematische Verdichtung."
    }


def format_top_topics(top_topics):
    if not top_topics:
        return "Keine dominanten Kritik-Themen in dieser Woche."
    lines = []
    for topic, count in top_topics:
        lines.append(f"- **{topic}** ({count})")
    return "\n".join(lines)

def pick_focus_week(metrics: dict, weeks_for_range: list[str], min_comments: int = 50) -> str:
    """
    Pick a focus week that is recent AND has enough volume.
    Uses sentiment_trend counts (most reliable aggregate).
    """
    # build total comment count per week from sentiment_trend
    totals = {}
    for r in metrics.get("sentiment_trend", []):
        w = r.get("week")
        c = r.get("count", 0)
        if w:
            totals[w] = totals.get(w, 0) + int(c)

    # 1) newest week in range with >= min_comments
    for w in reversed(weeks_for_range):
        if totals.get(w, 0) >= min_comments:
            return w

    # 2) fallback: pick max-volume week within range
    if totals:
        candidates = {w: totals.get(w, 0) for w in weeks_for_range}
        return max(candidates, key=candidates.get)

    # 3) ultimate fallback: newest week
    return weeks_for_range[-1]



def main():
    metrics = load_metrics()

    escalation_list = metrics.get("escalation", [])
    if not escalation_list:
        raise ValueError("No 'escalation' found in aggregated_metrics.json (expected new schema).")

    # ---- NEW: Analysis range + focus week ----
    all_weeks = _sorted_weeks_from_records(escalation_list)
    if not all_weeks:
        raise ValueError("No weeks found in 'escalation' records.")

    # Use config LATEST_WEEKS if present, default 3 (but doesn't force "one week report" anymore)
    latest_weeks_cfg = _get_cfg_int("LATEST_WEEKS", 3)
    # Keep last N weeks for the report range (cap at available weeks)
    weeks_for_range = all_weeks[-latest_weeks_cfg:] if latest_weeks_cfg > 0 else all_weeks

    range_start = weeks_for_range[0]
    range_end = weeks_for_range[-1]

    # Focus week = newest week in range (used for status/weekly blocks)
    MIN_FOCUS_WEEK_COMMENTS = _get_cfg_int("MIN_FOCUS_WEEK_COMMENTS", 50)
    week = pick_focus_week(metrics, weeks_for_range, min_comments=MIN_FOCUS_WEEK_COMMENTS)


    escalation_by_week = _index_by_week(escalation_list)
    latest_esc = escalation_by_week.get(week, {})

    # Optional blocks
    criticism_structure_idx = _index_by_week(metrics.get("criticism_structure", []))
    emotion_context_idx = _index_by_week(metrics.get("emotion_context", []))
    trend_flags_idx = _index_by_week(metrics.get("trend_flags", []))

    cs = criticism_structure_idx.get(week, {})
    ec = emotion_context_idx.get(week, {})
    tf = trend_flags_idx.get(week, {})

    # Issues for this week
    issues = metrics.get("issues", [])
    issues_week = [i for i in issues if i.get("week") == week]

    critical_issues = sorted(
        [i for i in issues_week if i.get("intent_group") == "critical"],
        key=lambda x: x.get("comment_count", 0),
        reverse=True
    )[:5]

    supportive_issues = sorted(
        [i for i in issues_week if i.get("intent_group") == "supportive"],
        key=lambda x: x.get("comment_count", 0),
        reverse=True
    )[:5]

    classification = classify_status_for_week(
        escalation_level=latest_esc.get("level"),
        criticism_structure=cs.get("structure"),
    )

    # Scale anchor
    escalation_scale_text = "stable < 15%, watch < 30%, critical ≥ 30%"
    aggressive_ratio_pct = float(latest_esc.get("aggressive_ratio", 0.0)) * 100

    # Trend sentence (optional)
    trend_sentence = None
    if tf:
        trend_sentence = (
            f"Trend-Signal (ggü. Vorwoche): Negative-Stimmung **{tf.get('negative_trend','n/a')}** "
            f"(Δ {tf.get('negative_change','n/a')}); "
            f"Kritik-Intent **{tf.get('critical_intent_trend','n/a')}** "
            f"(Δ {tf.get('critical_intent_change','n/a')})."
        )

    # Emotion context (optional)
    emotion_sentence = None
    if ec:
        label = ec.get("emotion_label", "n/a")
        emotion_sentence = (
            f"Emotionskontext: Ø Emotion gesamt **{ec.get('avg_emotion_total','n/a')}**, "
            f"Ø negativ **{ec.get('avg_emotion_negative','n/a')}** "
            f"(Lift {ec.get('emotion_lift','n/a')}, Label: **{label}**)."
        )

    # Dominance/structure (optional)
    dominance_sentence = None
    if cs and cs.get("structure"):
        dominance_sentence = (
            f"Kritik-Struktur: **{cs.get('structure')}** "
            f"(Dominanz {float(cs.get('dominance', 0.0)):.2f}; Schwelle focused > 0.40)."
        )

    lines = []
    lines.append("# Community Sentiment Report – BiasedSkeptic\n")

    # Kurzfazit
    lines.append("## Kurzfazit\n")
    lines.append(f"**Bewertung:** {classification['status']}")
    lines.append(f"**Empfehlung:** {classification['action']}")
    lines.append(f"**Begründung:** {classification['reason']}\n")

    # Datengrundlage & Herleitung
    lines.append("## Datengrundlage & Herleitung\n")
    lines.append(
    f"**Analysezeitraum:** **{range_start}** bis **{range_end}** "
    f"(Fokus-Woche: **{week}**, Mindestvolumen: {MIN_FOCUS_WEEK_COMMENTS}, LATEST_WEEKS={latest_weeks_cfg})\n"
    )

    lines.append(
        f"- Aggressive Kritik (Fokus-Woche): **{aggressive_ratio_pct:.1f}%** "
        f"(Skala: {escalation_scale_text}; Level: **{latest_esc.get('level','n/a')}**)"
    )

    if dominance_sentence:
        lines.append(f"- {dominance_sentence}")
    else:
        lines.append("- Kritik-Struktur: **n/a** (criticism_structure fehlt oder keine kritischen Kommentare)")

    if emotion_sentence:
        lines.append(f"- {emotion_sentence}")
    else:
        lines.append("- Emotionskontext: **n/a** (emotion_context fehlt)")

    if trend_sentence:
        lines.append(f"\n{trend_sentence}")
    else:
        lines.append("\nTrend-Signal: **n/a** (trend_flags fehlen oder nur 1 Woche im Datensatz).")

    # Visuals
    lines.append("\n## Sentiment-Entwicklung\n")
    lines.append("![](sentiment_trend.png)\n")

    lines.append("\n## Intent-Entwicklung\n")
    lines.append("![](intent_shift.png)\n")

    # Kritik- & Trigger-Themen (pro Woche!)
    lines.append("\n## Kritik- & Trigger-Themen\n")
    top_topics = cs.get("top_topics") if cs else None

    if not top_topics:
        lines.append("Keine klaren Kritik-Cluster in dieser Fokus-Woche (zu wenige kritische Kommentare oder keine Topics).")
    else:
        lines.append(format_top_topics(top_topics))
        if cs.get("structure") == "focused":
            lines.append("\n**Einordnung (regelbasiert):** Kritik ist fokussiert → beobachten.")
        elif cs.get("structure") == "fragmented":
            lines.append("\n**Einordnung (regelbasiert):** Kritik ist fragmentiert → kein einzelner Trigger dominiert.")

    # Issues
    lines.append("\n## Top Issues (Fokus-Woche)\n")

    if not issues_week:
        lines.append("Keine Issues verfügbar (fehlende key_topics oder leerer Zeitraum).")
    else:
        if supportive_issues:
            lines.append("**Supportive (Support/Lob):**")
            for i in supportive_issues:
                lines.append(f"- **{i.get('topic')}**: {i.get('comment_count')} (Ø Emotion {i.get('avg_emotion')})")
            lines.append("")

        if critical_issues:
            lines.append("**Kritisch (Constructive/Aggressive):**")
            for i in critical_issues:
                lines.append(f"- **{i.get('topic')}**: {i.get('comment_count')} (Ø Emotion {i.get('avg_emotion')})")
        else:
            lines.append("Keine signifikanten kritischen Issues in dieser Fokus-Woche.")

    # Abschluss
    lines.append("\n## Interpretation & Empfehlung\n")
    lines.append(
        f"Status **{classification['status']}** (Fokus-Woche **{week}**), weil:\n"
        f"- Eskalation-Level = **{latest_esc.get('level','n/a')}** (aggressive Kritik {aggressive_ratio_pct:.1f}%)\n"
        f"- Kritik-Struktur = **{cs.get('structure','n/a')}**\n"
        f"- Trend-Signale = **{tf.get('negative_trend','n/a')}** (Sentiment), **{tf.get('critical_intent_trend','n/a')}** (Intent)\n"
        f"\n**Empfehlung:** {classification['action']}"
    )

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Report written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
