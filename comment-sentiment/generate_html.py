import pathlib
import markdown
import config

def _slugify_channel(handle: str) -> str:
    s = (handle or "").strip()
    if s.startswith("@"):
        s = s[1:]
    s = s.lower()
    s = "".join(ch for ch in s if ch.isalnum() or ch in ("-", "_"))
    return s or "channel"

CHANNEL_HANDLE = getattr(config, "CHANNEL_HANDLE", "")
CHANNEL_SLUG = _slugify_channel(CHANNEL_HANDLE)

# --- Pfade ---
BASE_DIR = pathlib.Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"

# Neuestes Report-MD für diesen Channel automatisch finden
md_files = sorted(OUTPUT_DIR.glob("report_*.md"))
if not md_files:
    raise FileNotFoundError(f"Kein Markdown-Report gefunden für Channel '{CHANNEL_HANDLE}' (slug: {CHANNEL_SLUG}).")

MD_FILE = md_files[-1]  # neuester Report für den Channel
HTML_FILE = OUTPUT_DIR / f"report_{CHANNEL_SLUG}.html"

# Markdown laden
with open(MD_FILE, "r", encoding="utf-8") as f:
    md_text = f.read()

# Markdown zu HTML konvertieren
html_body = markdown.markdown(md_text, extensions=["tables", "fenced_code"])

# HTML-Template
html_content = f"""
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <title>Community Sentiment Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 2rem; }}
        h1, h2, h3 {{ color: #333; }}
        table {{ border-collapse: collapse; width: 100%; margin-bottom: 1rem; }}
        table, th, td {{ border: 1px solid #ccc; }}
        th, td {{ padding: 0.5rem; text-align: left; }}
        pre {{ background: #f4f4f4; padding: 0.5rem; }}
        img {{ max-width: 100%; height: auto; }}
    </style>
</head>
<body>
{html_body}
</body>
</html>
"""

# HTML speichern
with open(HTML_FILE, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"HTML-Report erstellt: {HTML_FILE} (Quelle: {MD_FILE.name})")
