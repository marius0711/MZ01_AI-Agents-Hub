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


ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
OUTPUT_DIR = ROOT_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CHANNEL_HANDLE = getattr(config, "CHANNEL_HANDLE", "")
if not CHANNEL_HANDLE:
    raise ValueError("CHANNEL_HANDLE missing in config.py")
CHANNEL_SLUG = _slugify_channel(CHANNEL_HANDLE)

INPUT_PATH = DATA_DIR / f"aggregated_metrics_{CHANNEL_SLUG}.json"
OUTPUT_PATH = OUTPUT_DIR / f"intent_shift_{CHANNEL_SLUG}.png"


def main() -> None:
    with INPUT_PATH.open("r", encoding="utf-8") as f:
        metrics = json.load(f)

    intent_shift = metrics.get("intent_shift", [])
    if not intent_shift:
        raise ValueError("No 'intent_shift' found in aggregated metrics.")

    df = pd.DataFrame(intent_shift)

    df["week_period"] = pd.PeriodIndex(df["week"], freq="W")
    df = df.sort_values("week_period").reset_index(drop=True)

    def _week_label(p: pd.Period) -> str:
        iso = p.end_time.isocalendar()
        return f"KW {iso.week:02d} ({iso.year})"

    df["week_label"] = df["week_period"].apply(_week_label)

    order = df["week_label"].drop_duplicates().tolist()
    df["week_label"] = pd.Categorical(df["week_label"], categories=order, ordered=True)

    pivot = df.pivot(index="week_label", columns="intent_group", values="ratio").fillna(0)

    # -----------------------------
    # Plot
    # -----------------------------
    fig, ax = plt.subplots(figsize=(8, 4))

    COLOR_MAP = {
        "critical": "tab:red",
        "supportive": "tab:green",
        "neutral": "tab:orange",
        "constructive": "tab:blue",
        "mixed": "tab:blue",
        "other": "tab:gray",
    }

    # Plot each line with deterministic colors (instead of pivot.plot auto-colors)
    for group in pivot.columns:
        ax.plot(
            range(len(pivot.index)),
            pivot[group].values,
            marker="o",
            label=group,
            color=COLOR_MAP.get(str(group).lower(), "tab:gray"),
        )

    labels = list(pivot.index)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=30, ha="right")
    ax.set_xlim(-0.5, len(labels) - 0.5)

    title_suffix = CHANNEL_HANDLE if CHANNEL_HANDLE else CHANNEL_SLUG
    ax.set_title(f"Intent Shift in Community Comments – {title_suffix}")

    ax.set_xlabel("Woche")
    ax.set_ylabel("Anteil der Kommentare (%)")

    ax.set_ylim(0, 1)
    ax.yaxis.set_major_formatter(PercentFormatter(1.0))

    ax.grid(True, alpha=0.3)
    ax.legend(title="Intent Group", loc="upper left")

    fig.tight_layout()
    fig.savefig(OUTPUT_PATH, dpi=200, bbox_inches="tight")
    plt.close(fig)

    print(f"Intent shift plot written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
