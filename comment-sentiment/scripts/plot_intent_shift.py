import json
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

import config


def _slugify_channel(handle: str) -> str:
    """
    Turn a channel handle into a filesystem-safe slug.
    Example: "@timgabelofficial" -> "timgabelofficial"
    """
    s = (handle or "").strip()
    if s.startswith("@"):
        s = s[1:]
    s = s.lower()
    s = "".join(ch for ch in s if ch.isalnum() or ch in ("-", "_"))
    return s or "channel"


# -----------------------------
# Paths & Channel
# -----------------------------
BASE_DIR = Path(__file__).resolve().parent.parent  # comment-sentiment/
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CHANNEL_HANDLE = getattr(config, "CHANNEL_HANDLE", "")
CHANNEL_SLUG = _slugify_channel(CHANNEL_HANDLE)

INPUT_PATH = DATA_DIR / f"aggregated_metrics_{CHANNEL_SLUG}.json"
OUTPUT_PATH = OUTPUT_DIR / f"intent_shift_{CHANNEL_SLUG}.png"


# -----------------------------
# Main
# -----------------------------
def main() -> None:
    # --- Load metrics ---
    with INPUT_PATH.open("r", encoding="utf-8") as f:
        metrics = json.load(f)

    intent_shift = metrics.get("intent_shift", [])
    if not intent_shift:
        raise ValueError("No 'intent_shift' found in aggregated metrics.")

    df = pd.DataFrame(intent_shift)

    # --- Week handling (ISO-safe) ---
    df["week_period"] = pd.PeriodIndex(df["week"], freq="W")
    df = df.sort_values("week_period").reset_index(drop=True)

    def _week_label(p: pd.Period) -> str:
        iso = p.end_time.isocalendar()
        return f"KW {iso.week} ({iso.year})"

    df["week_label"] = df["week_period"].apply(_week_label)

    order = df["week_label"].drop_duplicates().tolist()
    df["week_label"] = pd.Categorical(df["week_label"], categories=order, ordered=True)

    # --- Pivot for plotting ---
    pivot = (
        df.pivot(index="week_label", columns="intent_group", values="ratio")
        .fillna(0)
    )

    # -----------------------------
    # Plot
    # -----------------------------
    fig, ax = plt.subplots(figsize=(8, 4))

    pivot.plot(kind="line", marker="o", ax=ax)

    title_suffix = CHANNEL_HANDLE if CHANNEL_HANDLE else CHANNEL_SLUG
    ax.set_title(f"Intent Shift in Community Comments – {title_suffix}")

    ax.set_xlabel("Woche")
    ax.set_ylabel("Anteil der Kommentare (%)")

    ax.set_ylim(0, 1)
    ax.yaxis.set_major_formatter(PercentFormatter(1.0))

    ax.grid(True, alpha=0.3)
    ax.legend(title="Intent Group", loc="upper left")

    ax.tick_params(axis="x", labelrotation=30)

    fig.tight_layout()
    fig.savefig(OUTPUT_PATH, dpi=200, bbox_inches="tight")
    plt.close(fig)

    print(f"Intent shift plot written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
