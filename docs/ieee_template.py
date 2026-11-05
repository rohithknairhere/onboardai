"""Make the supplied IEEE template usable by python-docx.

The template was saved as Strict Open XML, which uses purl.oclc.org namespaces.
python-docx only understands the Transitional namespaces, so it refuses to open
the file. This module rewrites the namespace URIs across every XML part, which
is the same conversion Word performs when a strict file is resaved as
transitional, and leaves everything else untouched.
"""
import re
import shutil
import zipfile
from pathlib import Path

STRICT_TO_TRANSITIONAL = {
    "http://purl.oclc.org/ooxml/wordprocessingml/main":
        "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "http://purl.oclc.org/ooxml/officeDocument/relationships":
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "http://purl.oclc.org/ooxml/officeDocument/math":
        "http://schemas.openxmlformats.org/officeDocument/2006/math",
    "http://purl.oclc.org/ooxml/drawingml/main":
        "http://schemas.openxmlformats.org/drawingml/2006/main",
    "http://purl.oclc.org/ooxml/drawingml/wordprocessingDrawing":
        "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
    "http://purl.oclc.org/ooxml/drawingml/picture":
        "http://schemas.openxmlformats.org/drawingml/2006/picture",
    "http://purl.oclc.org/ooxml/drawingml/chart":
        "http://schemas.openxmlformats.org/drawingml/2006/chart",
    "http://purl.oclc.org/ooxml/drawingml/diagram":
        "http://schemas.openxmlformats.org/drawingml/2006/diagram",
    "http://purl.oclc.org/ooxml/officeDocument/extendedProperties":
        "http://schemas.openxmlformats.org/officeDocument/2006/extended-properties",
    "http://purl.oclc.org/ooxml/officeDocument/customProperties":
        "http://schemas.openxmlformats.org/officeDocument/2006/custom-properties",
    "http://purl.oclc.org/ooxml/officeDocument/docPropsVTypes":
        "http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes",
    "http://purl.oclc.org/ooxml/officeDocument/bibliography":
        "http://schemas.openxmlformats.org/officeDocument/2006/bibliography",
    "http://purl.oclc.org/ooxml/officeDocument/customXml":
        "http://schemas.openxmlformats.org/officeDocument/2006/customXml",
}


def to_transitional(source: Path, target: Path) -> Path:
    """Rewrite a strict OOXML docx into a transitional one."""
    source, target = Path(source), Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(source) as zin:
        items = [(i, zin.read(i.filename)) for i in zin.infolist()]

    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zout:
        for info, data in items:
            if info.filename.endswith((".xml", ".rels")):
                text = data.decode("utf-8", "replace")
                for strict, transitional in STRICT_TO_TRANSITIONAL.items():
                    text = text.replace(strict, transitional)
                data = text.encode("utf-8")
            zout.writestr(info, data)
    return target


def open_template(source: Path, workdir: Path):
    """Return a python-docx Document for the supplied template."""
    import docx
    converted = to_transitional(source, workdir / "_ieee_transitional.docx")
    return docx.Document(str(converted)), converted


def clear_body(document):
    """Remove every paragraph and table, keeping styles and section setup."""
    body = document.element.body
    sectPr = body.find(
        "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}sectPr")
    for child in list(body):
        if child is not sectPr:
            body.remove(child)
    return document


def available_styles(document):
    return sorted(s.style_id for s in document.styles if s.style_id)


if __name__ == "__main__":
    import sys
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
        r"C:\Users\Rohith\Downloads\Final project paper template.docx")
    out = Path(__file__).resolve().parent / "_build"
    doc, path = open_template(src, out)
    print(f"converted: {path}")
    print(f"paragraphs: {len(doc.paragraphs)}, tables: {len(doc.tables)}")
    print("styles:", ", ".join(available_styles(doc)))
