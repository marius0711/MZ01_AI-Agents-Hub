import json
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

import config


def _slugify_channel(handle: str) -> str:
    s = (handle or "").strip()
    if s.startswith("@"):
        s = s[1:]
    s = s.lower()
    s = "".join(ch for ch in s if ch.isalnum() or ch in ("-", "_"))
    return s or "channel"


# -----------------------------
# Paths & Channel
# -----------------------------
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
OUTPUT_DIR = ROOT_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CHANNEL_HANDLE = getattr(config, "CHANNEL_HANDLE", "")
CHANNEL_SLUG = _slugify_channel(CHANNEL_HANDLE)
if not CHANNEL_HANDLE:
    raise ValueError("CHANNEL_HANDLE missing in config.py")
INPUT_PATH = DATA_DIR / f"aggregated_metrics_{CHANNEL_SLUG}.json"
OUTPUT_PATH = OUTPUT_DIR / f"sentiment_trend_{CHANNEL_SLUG}.png"


def main() -> None:
    # --- Load metrics ---
    with INPUT_PATH.open("r", encoding="utf-8") as f:
        metrics = json.load(f)

    sentiment_trend = metrics.get("sentiment_trend", [])
    if not sentiment_trend:
        raise ValueError("No 'sentiment_trend' found in aggregated metrics.")

    df = pd.DataFrame(sentiment_trend)

    # --- Week handling (ISO-safe) ---
    df["week_period"] = pd.PeriodIndex(df["week"], freq="W")
    df = df.sort_values("week_period").reset_index(drop=True)

    def _week_label(p: pd.Period) -> str:
        iso = p.end_time.isocalendar()
        return f"KW {iso.week:02d} ({iso.year})"

    df["week_label"] = df["week_period"].apply(_week_label)

    order = df["week_label"].drop_duplicates().tolist()
    df["week_label"] = pd.Categorical(df["week_label"], categories=order, ordered=True)

    # --- Pivot: week x sentiment ---
    pivot = df.pivot(index="week_label", columns="sentiment", values="ratio").fillna(0)

    # -----------------------------
    # Plot
    # -----------------------------
    fig, ax = plt.subplots(figsize=(8, 4))
    
    COLOR_MAP = {
        "negative": "tab:red",
        "neutral": "tab:orange",
        "positive": "tab:green",
    }
    
    for sentiment in pivot.columns:
        ax.plot(
            range(len(pivot.index)),
            pivot[sentiment].values,
            marker="o",
            label=sentiment,
            color=COLOR_MAP.get(sentiment, "gray"),
        )


    # Force all x tick labels to show
    labels = list(pivot.index)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=30, ha="right")
    ax.set_xlim(-0.5, len(labels) - 0.5)

    ax.set_title("Community Sentiment Trend (Top-Level Comments)")
    ax.set_xlabel("Woche")
    ax.set_ylabel("Anteil der Kommentare (%)")

    ax.set_ylim(0, 1)
    ax.yaxis.set_major_formatter(PercentFormatter(1.0))

    ax.grid(True, alpha=0.3)
    ax.legend(title="Sentiment", loc="upper left")

    fig.tight_layout()
    fig.savefig(OUTPUT_PATH, dpi=200, bbox_inches="tight")
    plt.close(fig)

    print(f"Sentiment trend plot written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
