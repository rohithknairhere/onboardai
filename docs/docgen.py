"""Render one document definition to both .docx and LaTeX.

Both outputs come from the same structure so the Word file and the Overleaf
source cannot drift apart.

A document is a dict:
    title, subtitle, authors, meta, sections, references

A section is a dict with any of:
    heading, level, paras, bullets, numbered, table, figure, code
"""
import re
from pathlib import Path

LATEX_ESCAPES = {
    "\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$",
    "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}",
    "~": r"\textasciitilde{}", "^": r"\textasciicircum{}",
}


def tex_escape(text):
    text = str(text)
    out = []
    for ch in text:
        out.append(LATEX_ESCAPES.get(ch, ch))
    s = "".join(out)
    # Inline emphasis written as *word* becomes \textit{word}
    s = re.sub(r"\*([^*]+)\*", r"\\textit{\1}", s)
    return s


# ---------------------------------------------------------------------------
# DOCX
# ---------------------------------------------------------------------------

def render_docx(doc, path):
    import docx
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Pt, Inches, RGBColor

    d = docx.Document()

    for section in d.sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.9)
        section.right_margin = Inches(0.9)

    normal = d.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(10.5)
    normal.paragraph_format.space_after = Pt(6)

    title = d.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run(doc["title"])
    run.font.size = Pt(18)
    run.font.bold = True

    if doc.get("subtitle"):
        sub = d.add_paragraph()
        sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = sub.add_run(doc["subtitle"])
        r.font.size = Pt(11.5)
        r.font.color.rgb = RGBColor(0x44, 0x44, 0x44)

    if doc.get("authors"):
        for a in doc["authors"]:
            p = d.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_after = Pt(2)
            r = p.add_run(f"{a['name']} ({a['roll']}), {a['role']}")
            r.font.size = Pt(10)
        p = d.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(doc.get("affiliation", ""))
        r.font.size = Pt(9.5)
        r.font.italic = True

    if doc.get("meta"):
        table = d.add_table(rows=0, cols=2)
        table.style = "Table Grid"
        for label, value in doc["meta"]:
            cells = table.add_row().cells
            cells[0].text = label
            cells[1].text = value
            for r_i, cell in enumerate(cells):
                for p in cell.paragraphs:
                    for run in p.runs:
                        run.font.size = Pt(9.5)
                        run.font.bold = (r_i == 0)
        d.add_paragraph()

    for sec in doc["sections"]:
        if sec.get("heading"):
            level = sec.get("level", 1)
            h = d.add_heading(sec["heading"], level=level)
            for run in h.runs:
                run.font.color.rgb = RGBColor(0, 0, 0)
                run.font.name = "Times New Roman"
                run.font.size = Pt(14 if level == 1 else 12)

        for para in sec.get("paras", []):
            p = d.add_paragraph(para)
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

        for item in sec.get("bullets", []):
            d.add_paragraph(item, style="List Bullet")

        for item in sec.get("numbered", []):
            d.add_paragraph(item, style="List Number")

        if sec.get("table"):
            t = sec["table"]
            rows = [t["header"]] + t["rows"]
            table = d.add_table(rows=len(rows), cols=len(rows[0]))
            table.style = "Table Grid"
            for r, row in enumerate(rows):
                for c, value in enumerate(row):
                    cell = table.cell(r, c)
                    cell.text = str(value)
                    for p in cell.paragraphs:
                        p.paragraph_format.space_after = Pt(0)
                        for run in p.runs:
                            run.font.size = Pt(9)
                            run.font.bold = (r == 0)
            if t.get("caption"):
                cap = d.add_paragraph()
                cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
                r = cap.add_run(t["caption"])
                r.font.size = Pt(9)
                r.font.italic = True

        if sec.get("figure"):
            fig = sec["figure"]
            fp = Path(fig["path"])
            if fp.exists():
                d.add_picture(str(fp), width=Inches(5.8))
                d.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
                cap = d.add_paragraph()
                cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
                r = cap.add_run(fig.get("caption", ""))
                r.font.size = Pt(9)
                r.font.italic = True

        if sec.get("code"):
            p = d.add_paragraph()
            r = p.add_run(sec["code"])
            r.font.name = "Consolas"
            r.font.size = Pt(9)

    if doc.get("references"):
        h = d.add_heading("References", level=1)
        for run in h.runs:
            run.font.color.rgb = RGBColor(0, 0, 0)
            run.font.name = "Times New Roman"
            run.font.size = Pt(14)
        for i, ref in enumerate(doc["references"], 1):
            p = d.add_paragraph(f"[{i}] {ref}")
            p.paragraph_format.left_indent = Inches(0.35)
            p.paragraph_format.first_line_indent = Inches(-0.35)
            for run in p.runs:
                run.font.size = Pt(9.5)

    Path(path).parent.mkdir(parents=True, exist_ok=True)
    d.save(str(path))
    return path


# ---------------------------------------------------------------------------
# LaTeX
# ---------------------------------------------------------------------------

IEEE_PREAMBLE = r"""\documentclass[conference]{IEEEtran}
\IEEEoverridecommandlockouts
\usepackage{cite}
\usepackage{amsmath,amssymb,amsfonts}
\usepackage{graphicx}
\usepackage{textcomp}
\usepackage{xcolor}
\usepackage{booktabs}
\usepackage{array}
\def\BibTeX{{\rm B\kern-.05em{\sc i\kern-.025em b}\kern-.08em T\kern-.1667em\lower.7ex\hbox{E}\kern-.125emX}}
\begin{document}
"""

REPORT_PREAMBLE = r"""\documentclass[11pt,a4paper]{article}
\usepackage[margin=2.2cm]{geometry}
\usepackage{times}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{array}
\usepackage{longtable}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage{titlesec}
\titleformat{\section}{\large\bfseries}{\thesection}{1em}{}
\titleformat{\subsection}{\normalsize\bfseries}{\thesubsection}{1em}{}
\setlength{\parskip}{0.5em}
\setlength{\parindent}{0pt}
\begin{document}
"""


def strip_table_number(caption):
    """Remove a typed 'Table I.' prefix.

    Both Word's table head style and LaTeX's \\caption number themselves, so a
    typed number appears twice.
    """
    if not caption:
        return caption
    if caption.lower().startswith("table "):
        for marker in (". ", ".\t", ": "):
            head = caption[:14]
            if marker in head:
                return caption.split(marker, 1)[1]
    return caption


def _latex_table(t, style):
    header = t["header"]
    rows = t["rows"]
    ncol = len(header)
    widths = t.get("widths")

    # In a two column IEEE paper a wide table must use the starred environment,
    # otherwise it is confined to one column and overflows.
    ieee = style == "ieee"
    wide = ieee and ncol >= 3
    env = "table*" if wide else "table"
    # table* spans the full text width; a single column table is bounded by
    # \linewidth, which inside a column is the column width.
    unit = "\\textwidth" if wide else "\\linewidth"

    if widths:
        total = sum(widths)
        # Leave room for the inter column padding that array adds per column.
        scale = 0.94 / total if total else 1.0
        spec = "".join(f"p{{{w * scale:.3f}{unit}}}" for w in widths)
    else:
        spec = "".join(f"p{{{0.94 / ncol:.3f}{unit}}}" for _ in range(ncol))

    out = [f"\\begin{{{env}}}[!t]", "\\centering"]
    if t.get("caption"):
        out.append(f"\\caption{{{tex_escape(strip_table_number(t['caption']))}}}")
    out.append("\\footnotesize" if ieee else "\\small")
    out.append("\\setlength{\\tabcolsep}{3pt}")
    out.append(f"\\begin{{tabular}}{{{spec}}}")
    out.append("\\toprule")
    out.append(" & ".join(f"\\textbf{{{tex_escape(h)}}}" for h in header) + r" \\")
    out.append("\\midrule")
    for row in rows:
        out.append(" & ".join(tex_escape(c) for c in row) + r" \\")
    out.append("\\bottomrule")
    out.append("\\end{tabular}")
    out.append(f"\\end{{{env}}}")
    return "\n".join(out)


def render_latex(doc, path, style="report"):
    L = [IEEE_PREAMBLE if style == "ieee" else REPORT_PREAMBLE]

    if style == "ieee":
        L.append(f"\\title{{{tex_escape(doc['title'])}}}\n")

        blocks = []
        for a in doc["authors"]:
            blocks.append(
                "\\IEEEauthorblockN{%s}\n\\IEEEauthorblockA{\\textit{%s} \\\\\n%s \\\\\n%s \\\\\n%s}"
                % (tex_escape(a["name"]), tex_escape(a["role"]),
                   tex_escape(doc.get("dept", "")), tex_escape(doc.get("org", "")),
                   tex_escape(a["roll"])))

        # Two authors per row, so four authors form a two by two block rather
        # than being squeezed across a single row.
        per_row = 2
        rows = [blocks[i:i + per_row] for i in range(0, len(blocks), per_row)]
        author_body = "\n\\linebreak\n".join("\n\\and\n".join(r) for r in rows)
        L.append("\\author{\n" + author_body + "\n}\n")
        L.append("\\maketitle\n")
    else:
        L.append(f"\\title{{\\textbf{{{tex_escape(doc['title'])}}}}}")
        authors = " \\\\ ".join(
            f"{tex_escape(a['name'])} ({tex_escape(a['roll'])}), {tex_escape(a['role'])}"
            for a in doc.get("authors", []))
        L.append(f"\\author{{{authors}}}")
        L.append("\\date{}")
        L.append("\\maketitle\n")
        if doc.get("subtitle"):
            L.append("\\begin{center}\\itshape " + tex_escape(doc["subtitle"]) +
                     "\\end{center}\n")

    if doc.get("meta"):
        L.append("\\begin{tabular}{p{0.26\\linewidth}p{0.66\\linewidth}}")
        L.append("\\toprule")
        for label, value in doc["meta"]:
            L.append(f"\\textbf{{{tex_escape(label)}}} & {tex_escape(value)} \\\\")
        L.append("\\bottomrule")
        L.append("\\end{tabular}\n")

    for sec in doc["sections"]:
        if sec.get("heading"):
            cmd = "section" if sec.get("level", 1) == 1 else "subsection"
            L.append(f"\\{cmd}{{{tex_escape(sec['heading'])}}}")

        for para in sec.get("paras", []):
            L.append(tex_escape(para) + "\n")

        if sec.get("bullets"):
            L.append("\\begin{itemize}[leftmargin=*,itemsep=2pt]")
            for item in sec["bullets"]:
                L.append(f"  \\item {tex_escape(item)}")
            L.append("\\end{itemize}\n")

        if sec.get("numbered"):
            L.append("\\begin{enumerate}[leftmargin=*,itemsep=2pt]")
            for item in sec["numbered"]:
                L.append(f"  \\item {tex_escape(item)}")
            L.append("\\end{enumerate}\n")

        if sec.get("table"):
            L.append(_latex_table(sec["table"], style))
            L.append("")

        if sec.get("figure"):
            fig = sec["figure"]
            name = Path(fig["path"]).name
            L.append("\\begin{figure}[htbp]")
            L.append("\\centering")
            L.append(f"\\includegraphics[width=\\linewidth]{{{name}}}")
            if fig.get("caption"):
                L.append(f"\\caption{{{tex_escape(fig['caption'])}}}")
            L.append("\\end{figure}\n")

        if sec.get("code"):
            L.append("\\begin{verbatim}")
            L.append(sec["code"])
            L.append("\\end{verbatim}\n")

    if doc.get("references"):
        L.append("\\begin{thebibliography}{99}")
        for i, ref in enumerate(doc["references"], 1):
            L.append(f"\\bibitem{{b{i}}} {tex_escape(ref)}")
        L.append("\\end{thebibliography}\n")

    L.append("\\end{document}")

    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(L), encoding="utf-8")
    return path
