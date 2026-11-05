"""Convert the project's markdown documents to PDF.

    backend/venv/Scripts/python.exe docs/md_to_pdf.py

Handles the subset of markdown actually used in this project: headings,
paragraphs, bullet and numbered lists, pipe tables, fenced code blocks,
horizontal rules, and inline bold, italic and code.
"""
import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate, Frame, KeepTogether, PageBreak, PageTemplate, Paragraph,
    Preformatted, Spacer, Table, TableStyle,
)

ROOT = Path(__file__).resolve().parent.parent

INK = colors.HexColor("#1A1A1A")
MUTED = colors.HexColor("#5A5A5A")
ACCENT = colors.HexColor("#8A6D1F")
RULE = colors.HexColor("#D8D4CC")
CODE_BG = colors.HexColor("#F4F2ED")

_base = getSampleStyleSheet()

S = {
    "h1": ParagraphStyle("h1", parent=_base["Normal"], fontName="Helvetica-Bold",
                         fontSize=17, leading=21, textColor=INK,
                         spaceBefore=14, spaceAfter=8),
    "h2": ParagraphStyle("h2", parent=_base["Normal"], fontName="Helvetica-Bold",
                         fontSize=13, leading=17, textColor=INK,
                         spaceBefore=12, spaceAfter=6),
    "h3": ParagraphStyle("h3", parent=_base["Normal"], fontName="Helvetica-Bold",
                         fontSize=11, leading=14, textColor=ACCENT,
                         spaceBefore=10, spaceAfter=4),
    "h4": ParagraphStyle("h4", parent=_base["Normal"], fontName="Helvetica-Bold",
                         fontSize=10, leading=13, textColor=MUTED,
                         spaceBefore=8, spaceAfter=3),
    "body": ParagraphStyle("body", parent=_base["Normal"], fontSize=9.6, leading=14,
                           textColor=INK, alignment=TA_JUSTIFY, spaceAfter=7),
    "bullet": ParagraphStyle("bullet", parent=_base["Normal"], fontSize=9.6, leading=13.5,
                             textColor=INK, leftIndent=12, bulletIndent=2, spaceAfter=3),
    "cell": ParagraphStyle("cell", parent=_base["Normal"], fontSize=8.3, leading=11,
                           textColor=INK),
    "cellb": ParagraphStyle("cellb", parent=_base["Normal"], fontName="Helvetica-Bold",
                            fontSize=8.3, leading=11, textColor=INK),
    "code": ParagraphStyle("code", parent=_base["Normal"], fontName="Courier",
                           fontSize=8, leading=10.5, textColor=colors.HexColor("#2A2A2A")),
    "title": ParagraphStyle("title", parent=_base["Normal"], fontName="Helvetica-Bold",
                            fontSize=22, leading=27, textColor=INK, spaceAfter=4),
}


def inline(text):
    """Convert inline markdown to reportlab markup, escaping everything else."""
    text = html.escape(text, quote=False)
    text = re.sub(r"`([^`]+)`",
                  r'<font face="Courier" size="8.6" color="#7A4E1F">\1</font>', text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<i>\1</i>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<link href="\2" color="#3B5A7A">\1</link>',
                  text)
    return text


def _table(rows):
    data = []
    for r_i, row in enumerate(rows):
        data.append([Paragraph(inline(c), S["cellb"] if r_i == 0 else S["cell"])
                     for c in row])

    ncols = max(len(r) for r in data)
    for r in data:
        while len(r) < ncols:
            r.append(Paragraph("", S["cell"]))

    avail = 166 * mm
    t = Table(data, colWidths=[avail / ncols] * ncols, repeatRows=1)
    style = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
        ("BOX", (0, 0), (-1, -1), 0.5, RULE),
        ("LINEBELOW", (0, 0), (-1, -2), 0.3, RULE),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EDE9E1")),
        ("LINEBELOW", (0, 0), (-1, 0), 0.7, MUTED),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            style.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#FAF9F6")))
    t.setStyle(TableStyle(style))
    return t


def parse(md_text):
    story = []
    lines = md_text.split("\n")
    i = 0
    first_heading = True

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        # fenced code
        if stripped.startswith("```"):
            i += 1
            block = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                block.append(lines[i])
                i += 1
            i += 1
            if block:
                pre = Preformatted("\n".join(block), S["code"])
                wrapper = Table([[pre]], colWidths=[166 * mm])
                wrapper.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), CODE_BG),
                    ("BOX", (0, 0), (-1, -1), 0.4, RULE),
                    ("LEFTPADDING", (0, 0), (-1, -1), 7),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]))
                story.append(wrapper)
                story.append(Spacer(1, 7))
            continue

        # horizontal rule
        if re.fullmatch(r"-{3,}|\*{3,}|_{3,}", stripped):
            story.append(Spacer(1, 4))
            story.append(Table([[""]], colWidths=[166 * mm], rowHeights=[0.6],
                               style=TableStyle([("BACKGROUND", (0, 0), (-1, -1), RULE)])))
            story.append(Spacer(1, 8))
            i += 1
            continue

        # table
        if stripped.startswith("|") and i + 1 < len(lines) and \
                re.match(r"^\s*\|[\s:\-|]+\|\s*$", lines[i + 1]):
            rows = []
            header = [c.strip() for c in stripped.strip("|").split("|")]
            rows.append(header)
            i += 2
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            story.append(_table(rows))
            story.append(Spacer(1, 9))
            continue

        # headings
        m = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if m:
            level = len(m.group(1))
            text = m.group(2)
            if level == 1 and first_heading:
                story.append(Paragraph(inline(text), S["title"]))
                first_heading = False
            else:
                if level == 1:
                    story.append(PageBreak())
                key = f"h{min(level, 4)}"
                story.append(Paragraph(inline(text), S[key]))
            i += 1
            continue

        # bullets
        if re.match(r"^[-*+]\s+", stripped):
            items = []
            while i < len(lines) and re.match(r"^\s*[-*+]\s+", lines[i]):
                items.append(re.sub(r"^\s*[-*+]\s+", "", lines[i]))
                i += 1
            for item in items:
                story.append(Paragraph("&bull;&nbsp;&nbsp;" + inline(item), S["bullet"]))
            story.append(Spacer(1, 4))
            continue

        # numbered
        if re.match(r"^\d+[.)]\s+", stripped):
            n = 0
            while i < len(lines) and re.match(r"^\s*\d+[.)]\s+", lines[i]):
                n += 1
                item = re.sub(r"^\s*\d+[.)]\s+", "", lines[i])
                story.append(Paragraph(f"{n}.&nbsp;&nbsp;" + inline(item), S["bullet"]))
                i += 1
            story.append(Spacer(1, 4))
            continue

        # paragraph, joining wrapped lines
        buf = [stripped]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(
                r"^\s*(#{1,6}\s|[-*+]\s|\d+[.)]\s|\||```|-{3,})", lines[i]):
            buf.append(lines[i].strip())
            i += 1
        story.append(Paragraph(inline(" ".join(buf)), S["body"]))

    return story


def _page(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(RULE)
    canvas.setLineWidth(0.5)
    canvas.line(22 * mm, 15 * mm, 188 * mm, 15 * mm)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(22 * mm, 10.5 * mm, doc.docTitle)
    canvas.drawRightString(188 * mm, 10.5 * mm, f"Page {doc.page}")
    canvas.restoreState()


def convert(md_path, pdf_path, title=None):
    md_path, pdf_path = Path(md_path), Path(pdf_path)
    text = md_path.read_text(encoding="utf-8")

    doc = BaseDocTemplate(
        str(pdf_path), pagesize=A4,
        leftMargin=22 * mm, rightMargin=22 * mm,
        topMargin=18 * mm, bottomMargin=20 * mm,
        title=title or md_path.stem)
    doc.docTitle = title or md_path.stem

    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="main")
    doc.addPageTemplates([PageTemplate(id="all", frames=[frame], onPage=_page)])

    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    doc.build(parse(text))
    return pdf_path


TARGETS = [
    (ROOT / "README.md", ROOT / "docs" / "pdf" / "README.pdf",
     "OnboardAI README"),
    (ROOT / "docs" / "PROJECT_GUIDE.md", ROOT / "docs" / "pdf" / "Project_Guide.pdf",
     "OnboardAI Project Guide"),
    (ROOT / "docs" / "CODEBASE_GUIDE.md", ROOT / "docs" / "pdf" / "Codebase_Guide.pdf",
     "OnboardAI Codebase Guide"),
    (ROOT / "backend" / "ml" / "artifacts" / "data_report.md",
     ROOT / "docs" / "pdf" / "Data_Report.pdf", "OnboardAI Data Report"),
    (ROOT / "backend" / "ml" / "artifacts" / "test_report.md",
     ROOT / "docs" / "pdf" / "Test_Report.pdf", "OnboardAI Test Report"),
    (ROOT / "backend" / "ml" / "artifacts" / "eda" / "observations.md",
     ROOT / "docs" / "pdf" / "EDA_Observations.pdf", "OnboardAI EDA Observations"),
]


def main():
    for src, dst, title in TARGETS:
        if not src.exists():
            print(f"  skipped (missing): {src.name}")
            continue
        convert(src, dst, title)
        print(f"  {dst.name}  ({dst.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
