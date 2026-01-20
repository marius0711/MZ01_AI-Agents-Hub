from __future__ import annotations

from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted


def markdown_to_simple_pdf(md_text: str, pdf_path: str | Path) -> Path:
    """
    Compact PDF export for scanning:
    - Smaller fonts
    - Tight spacing
    - No heavy markdown support by design (we keep it robust)
    """
    pdf_path = Path(pdf_path)
    pdf_path.parent.mkdir(parents=True, exist_ok=True)

    styles = getSampleStyleSheet()

    h1 = ParagraphStyle("H1c", parent=styles["Heading1"], fontSize=14, leading=16, spaceAfter=6)
    h2 = ParagraphStyle("H2c", parent=styles["Heading2"], fontSize=11, leading=13, spaceAfter=4)
    normal = ParagraphStyle("Nc", parent=styles["BodyText"], fontSize=9, leading=11, spaceAfter=1)
    mono = ParagraphStyle("Mc", parent=styles["BodyText"], fontName="Courier", fontSize=8, leading=10)

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        topMargin=24,
        bottomMargin=24,
        leftMargin=28,
        rightMargin=28,
    )

    story = []
    blank_run = 0

    for raw_line in md_text.splitlines():
        line = raw_line.rstrip()

        if not line.strip():
            blank_run += 1
            # avoid huge white space: allow at most one blank spacer in a row
            if blank_run <= 1:
                story.append(Spacer(1, 4))
            continue

        blank_run = 0

        if line.startswith("# "):
            story.append(Paragraph(line[2:].strip(), h1))
            continue

        if line.startswith("## "):
            story.append(Paragraph(line[3:].strip(), h2))
            continue

        if line.startswith("http://") or line.startswith("https://"):
            story.append(Preformatted(line, mono))
            continue

        # bullets + numbered items: keep compact
        if line.lstrip().startswith(("-", "*")):
            line = "• " + line.lstrip()[1:].lstrip()
        story.append(Paragraph(line, normal))

    doc.build(story)
    return pdf_path
