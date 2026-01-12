import subprocess
import sys
import config

def _slugify_channel(handle: str) -> str:
    s = (handle or "").strip()
    if s.startswith("@"):
        s = s[1:]
    s = s.lower()
    s = "".join(ch for ch in s if ch.isalnum() or ch in ("-", "_"))
    return s or "channel"

def run(module: str) -> None:
    # uses current venv python
    cmd = [sys.executable, "-m", module]
    print(f"\n▶ Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

def main():
    channel_handle = getattr(config, "CHANNEL_HANDLE", "")
    channel_slug = _slugify_channel(channel_handle)
    print(f"Channel: {channel_handle}  (slug: {channel_slug})")

    # 1) compute metrics
    run("scripts.compute_metrics")

    # 2) plots
    run("scripts.plot_trends")        # sentiment trend
    run("scripts.plot_intent_shift")  # intent shift

    print("\n✅ Done. Outputs should be in:")
    print(f"  data/aggregated_metrics_{channel_slug}.json")
    print(f"  output/sentiment_trend_{channel_slug}.png")
    print(f"  output/intent_shift_{channel_slug}.png")

if __name__ == "__main__":
    main()
