"""Build the final review study pack as PDFs.

    backend/venv/Scripts/python.exe docs/build_final_review_pdfs.py

Writes to docs/pdf/final_review/. Uses the converter in md_to_pdf.py, after
joining wrapped list items onto one line, which that converter expects.
"""
import re
import sys
import tempfile
from pathlib import Path

DOCS = Path(__file__).resolve().parent
ROOT = DOCS.parent
OUT = DOCS / "pdf" / "final_review"

sys.path.insert(0, str(DOCS))
from md_to_pdf import convert  # noqa: E402

PACK = [
    (DOCS / "TEAM_STUDY_GUIDE.md", "1_Team_Study_Guide.pdf", "OnboardAI Team Study Guide"),
    (DOCS / "FINAL_REVIEW_DEMO.md", "2_Final_Review_Demo.pdf", "OnboardAI Final Review Demo"),
    (DOCS / "PROJECT_GUIDE.md", "3_Project_Guide.pdf", "OnboardAI Project Guide"),
    (DOCS / "FINAL_EVALUATION.md", "4_Final_Evaluation.pdf", "OnboardAI Final Evaluation"),
    (ROOT / "README.md", "5_README.pdf", "OnboardAI README"),
]

_LIST_ITEM = re.compile(r"^\s*([-*+]|\d+[.)])\s+")


def join_wrapped_items(text: str) -> str:
    """Fold indented continuation lines into the list item above them."""
    out = []
    in_code = False
    seen_title = False
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code = not in_code
            out.append(stripped)  # un-indent fences so they are recognised
            continue
        if in_code:
            out.append(line[3:] if line.startswith("   ") else line)
            continue
        heading = re.match(r"^(#{1,6})\s+(.*)$", line)
        if heading:
            # The converter starts a new page at every level-1 heading, which
            # leaves half-empty pages. Keep the title, step every other heading
            # down one level so the pack reads continuously.
            if seen_title:
                level = min(len(heading.group(1)) + 1, 4)
                line = "#" * level + " " + heading.group(2)
            seen_title = True
            out.append(line)
            continue
        is_continuation = (
            out and stripped and line.startswith("  ") and not _LIST_ITEM.match(line)
            and _LIST_ITEM.match(out[-1] or "")
        )
        if is_continuation:
            out[-1] = out[-1].rstrip() + " " + stripped
        else:
            out.append(line)
    return "\n".join(out)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        for source, name, title in PACK:
            if not source.exists():
                print(f"  skipped {source.name} (missing)")
                continue
            prepared = Path(tmp) / source.name
            prepared.write_text(join_wrapped_items(source.read_text(encoding="utf-8")),
                                encoding="utf-8")
            convert(prepared, OUT / name, title=title)
            print(f"  wrote {name}")
    print(f"\nStudy pack in {OUT}")


if __name__ == "__main__":
    main()
