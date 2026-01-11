import json
from pathlib import Path
from datetime import datetime

import pandas as pd
import matplotlib.pyplot as plt

# --- paths ---
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

INPUT_PATH = DATA_DIR / "aggregated_metrics.json"
OUTPUT_PATH = OUTPUT_DIR / "sentiment_trend.png"


def load_data():
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    metrics = load_data()
    df = pd.DataFrame(metrics["sentiment_trend"])

    # ✅ robust ordering key
    df["week_period"] = pd.PeriodIndex(df["week"], freq="W")
    df = df.sort_values("week_period").reset_index(drop=True)

    # Pivot: week x sentiment
    pivot = df.pivot(index="week_period", columns="sentiment", values="ratio").fillna(0)

    # --- X labels: KW + Jahr (Ende der Woche) ---
    week_labels = [
        f"KW {p.end_time.isocalendar()[1]} ({p.end_time.year})"
        for p in pivot.index
    ]
    pivot.index = week_labels

    # Plot
    plt.figure(figsize=(8, 4))
    pivot.plot(kind="line", marker="o")

    plt.title("Community Sentiment Trend (Top-Level Comments)")
    plt.ylabel("Share of Comments")
    plt.xlabel("Week")
    plt.ylim(0, 1)
    plt.grid(True, alpha=0.3)
    plt.legend(title="Sentiment")
    plt.xticks(rotation=45, ha="right")

    plt.tight_layout()
    plt.savefig(OUTPUT_PATH)
    plt.close()

    print(f"Sentiment trend plot written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
