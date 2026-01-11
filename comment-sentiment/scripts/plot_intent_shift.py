import json
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

INPUT_PATH = DATA_DIR / "aggregated_metrics.json"
OUTPUT_PATH = OUTPUT_DIR / "intent_shift.png"


def main():
    # --- Load metrics ---
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        metrics = json.load(f)

    df = pd.DataFrame(metrics["intent_shift"])

    # --- FIX 1: week -> echtes Period-Objekt (für saubere Chronologie) ---
    df["week_period"] = pd.PeriodIndex(df["week"], freq="W")

    # --- FIX 2: chronologisch sortieren ---
    df = df.sort_values("week_period").reset_index(drop=True)

    # --- FIX 3: saubere Kalenderwochen-Labels ---
    df["week_label"] = df["week_period"].apply(
        lambda p: f"KW {p.end_time.isocalendar()[1]} ({p.end_time.year})"
    )

    # --- FIX 4: Reihenfolge der X-Achse explizit fixieren ---
    order = df["week_label"].drop_duplicates().tolist()
    df["week_label"] = pd.Categorical(df["week_label"], categories=order, ordered=True)

    # --- Pivot für Plot ---
    pivot = df.pivot(
        index="week_label",
        columns="intent_group",
        values="ratio"
    ).fillna(0)

    # --- Plot ---
    plt.figure(figsize=(8, 4))
    pivot.plot(kind="line", marker="o")

    plt.title("Intent Shift in Community Comments")
    plt.ylabel("Share of Comments")
    plt.xlabel("Week")
    plt.ylim(0, 1)
    plt.grid(True, alpha=0.3)
    plt.legend(title="Intent Group")

    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(OUTPUT_PATH)
    plt.close()

    print(f"Intent shift plot written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
