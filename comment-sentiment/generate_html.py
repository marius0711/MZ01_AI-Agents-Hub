# generate_html.py
import pathlib
import markdown

# --- Pfade ---
BASE_DIR = pathlib.Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"

# Neuestes Report-MD automatisch finden
md_files = sorted(OUTPUT_DIR.glob("report_biasedskeptic_*.md"))
if not md_files:
    raise FileNotFoundError("Kein Markdown-Report gefunden.")

MD_FILE = md_files[-1]  # neuester Report
HTML_FILE = OUTPUT_DIR / "report_biasedskeptic.html"

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
