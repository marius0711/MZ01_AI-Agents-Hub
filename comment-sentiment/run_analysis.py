import os
import subprocess
import sys
from pathlib import Path

import config

BASE_DIR = Path(__file__).resolve().parent  # .../comment-sentiment


def _slugify_channel(handle: str) -> str:
    s = (handle or "").strip()
    if s.startswith("@"):
        s = s[1:]
    s = s.lower()
    s = "".join(ch for ch in s if ch.isalnum() or ch in ("-", "_"))
    return s or "channel"


def run(module: str) -> None:
    """
    Robust runner:
    - always uses the current venv interpreter (sys.executable)
    - forces cwd to the project folder (BASE_DIR), no matter where you run this from
    - ensures BASE_DIR is on PYTHONPATH so `-m scripts.*` and `import config` work reliably
    - prints only essentials; on failure prints stdout/stderr and key context
    """
    cmd = [sys.executable, "-m", module]

    env = os.environ.copy()
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(BASE_DIR) + (os.pathsep + existing if existing else "")

    try:
        subprocess.run(
            cmd,
            cwd=str(BASE_DIR),
            env=env,
            check=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"\nERROR: Module failed: {module}")
        print(f"Command: {' '.join(cmd)}")
        print(f"CWD: {BASE_DIR}")
        print(f"Python: {sys.executable}")
        print(f"PYTHONPATH: {env.get('PYTHONPATH', '')}")

        # Re-run with captured output for a readable error report
        r = subprocess.run(
            cmd,
            cwd=str(BASE_DIR),
            env=env,
            text=True,
            capture_output=True,
        )
        if r.stdout:
            print("\n--- STDOUT ---")
            print(r.stdout.strip())
        if r.stderr:
            print("\n--- STDERR ---")
            print(r.stderr.strip())

        raise SystemExit(e.returncode)


def main() -> None:
    channel_handle = getattr(config, "CHANNEL_HANDLE", "")
    if not channel_handle:
        raise ValueError("CHANNEL_HANDLE missing in config.py")

    channel_slug = _slugify_channel(channel_handle)
    print(f"Channel: {channel_handle} (slug: {channel_slug})")

    # 1) compute metrics
    run("scripts.compute_metrics")

    # 2) plots
    run("scripts.plot_trends")
    run("scripts.plot_intent_shift")

    print("Done.")


if __name__ == "__main__":
    main()
