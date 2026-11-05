"""Render a paper into the supplied IEEE Word template.

The template carries the IEEE paragraph styles and a sequence of section breaks
that produce the IEEE layout: a single column title block, a multi column author
block, then the two column body. Those breaks live inside paragraphs, so simply
deleting all paragraphs destroys the layout. This module lifts the page setup
out first, clears the body, then builds its own section breaks around the
content.

Three things the template does that must be respected:

1. Heading1, Heading2, references and bulletlist number themselves. Typing a
   number produces it twice.
2. The "table head" style also numbers itself, so a caption must not begin with
   "Table I.".
3. A table wider than one column has to sit in its own single column section,
   otherwise Word clips it at the column boundary.
"""
import copy
from pathlib import Path

from ieee_template import open_template

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def _qn(tag):
    return W + tag


def _page_setup(document):
    """Grab page size and margins from the template's final section."""
    sect = document.element.body.find(_qn("sectPr"))
    if sect is None:
        return None, None
    pgSz = sect.find(_qn("pgSz"))
    pgMar = sect.find(_qn("pgMar"))
    return (copy.deepcopy(pgSz) if pgSz is not None else None,
            copy.deepcopy(pgMar) if pgMar is not None else None)


def _clear(document):
    for child in list(document.element.body):
        document.element.body.remove(child)


def _make_sectPr(cols, pgSz, pgMar, continuous=True):
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement

    sectPr = OxmlElement("w:sectPr")
    if continuous:
        t = OxmlElement("w:type")
        t.set(qn("w:val"), "continuous")
        sectPr.append(t)
    if pgSz is not None:
        sectPr.append(copy.deepcopy(pgSz))
    if pgMar is not None:
        sectPr.append(copy.deepcopy(pgMar))
    c = OxmlElement("w:cols")
    c.set(qn("w:num"), str(cols))
    c.set(qn("w:space"), "425")
    if cols > 1:
        c.set(qn("w:equalWidth"), "1")
    sectPr.append(c)
    return sectPr


def _break(document, cols, pgSz, pgMar):
    """Append an empty paragraph that closes the current section."""
    from docx.oxml import OxmlElement

    p = OxmlElement("w:p")
    pPr = OxmlElement("w:pPr")
    pPr.append(_make_sectPr(cols, pgSz, pgMar))
    p.append(pPr)
    document.element.body.append(p)


def _para(document, text, style=None, center=False):
    p = document.add_paragraph()
    if style:
        try:
            p.style = document.styles[style]
        except KeyError:
            pass
    if text:
        p.add_run(text)
    if center:
        p.alignment = 1
    return p


def _set_table_width(table, total_emu, widths):
    """Fix column widths so Word does not reflow the table off the page."""
    from docx.oxml.ns import qn
    from docx.shared import Emu

    table.autofit = False
    tblPr = table._tbl.tblPr
    tblW = tblPr.find(qn("w:tblW"))
    if tblW is None:
        from docx.oxml import OxmlElement
        tblW = OxmlElement("w:tblW")
        tblPr.append(tblW)
    tblW.set(qn("w:type"), "dxa")
    tblW.set(qn("w:w"), str(int(total_emu / 635)))

    for i, frac in enumerate(widths):
        width = Emu(int(total_emu * frac))
        for row in table.rows:
            row.cells[i].width = width


def _table(document, spec, total_emu):
    from docx.shared import Pt

    if spec.get("caption"):
        # The style numbers itself, so any typed "Table I." prefix is stripped.
        caption = spec["caption"]
        for marker in (". ", ".\t"):
            if caption.lower().startswith("table ") and marker in caption[:12]:
                caption = caption.split(marker, 1)[1]
                break
        cap = _para(document, caption, "table head", center=True)

    rows = [spec["header"]] + spec["rows"]
    ncols = len(rows[0])
    table = document.add_table(rows=len(rows), cols=ncols)
    try:
        table.style = document.styles["Table Grid"]
    except KeyError:
        pass

    widths = spec.get("widths")
    if not widths or len(widths) != ncols:
        widths = [1.0 / ncols] * ncols
    total = sum(widths)
    widths = [w / total for w in widths]
    _set_table_width(table, total_emu, widths)

    for r, row in enumerate(rows):
        for c, value in enumerate(row):
            cell = table.cell(r, c)
            cell.text = ""
            p = cell.paragraphs[0]
            try:
                p.style = document.styles["table col head" if r == 0 else "table copy"]
            except KeyError:
                pass
            run = p.add_run(str(value))
            run.font.size = Pt(8)
    return table


def render(doc, template_path, out_path, workdir):
    from docx.shared import Inches

    document, _ = open_template(Path(template_path), Path(workdir))
    pgSz, pgMar = _page_setup(document)
    _clear(document)

    # A4 with the template margins leaves roughly 6.9 inches of usable width.
    full_width = int(Inches(6.9))

    # --- title, single column ------------------------------------------
    _para(document, doc["title"], "paper title", center=True)
    _break(document, 1, pgSz, pgMar)

    # --- authors, two columns with two authors in each ------------------
    authors = doc.get("authors", [])
    half = (len(authors) + 1) // 2
    for group in (authors[:half], authors[half:]):
        for a in group:
            block = (f"{a['name']}\n"
                     f"{a['role']}\n"
                     f"{doc.get('dept', '')}\n"
                     f"{doc.get('org', '')}\n"
                     f"{a['roll']}")
            _para(document, block, "Author", center=True)
        _break(document, 2, pgSz, pgMar)

    # --- body, two columns ---------------------------------------------
    for sec in doc["sections"]:
        if sec.get("heading"):
            _para(document, sec["heading"],
                  "Heading 1" if sec.get("level", 1) == 1 else "Heading 2")

        for text in sec.get("paras", []):
            _para(document, text, "Body Text")

        for item in sec.get("bullets", []):
            _para(document, item, "bullet list")

        for i, item in enumerate(sec.get("numbered", []), 1):
            _para(document, f"{i}) {item}", "Body Text")

        if sec.get("table"):
            # Wide tables get their own single column section so Word renders
            # them across the full page instead of clipping at the column edge.
            _break(document, 2, pgSz, pgMar)
            _table(document, sec["table"], full_width)
            _para(document, "", "Body Text")
            _break(document, 1, pgSz, pgMar)

        if sec.get("code"):
            _para(document, sec["code"], "Body Text")

    if doc.get("references"):
        _para(document, "References", "Heading 5")
        for ref in doc["references"]:
            _para(document, ref, "references")

    # Close the final two column section.
    final = _make_sectPr(2, pgSz, pgMar, continuous=False)
    document.element.body.append(final)

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    document.save(str(out_path))
    return out_path
