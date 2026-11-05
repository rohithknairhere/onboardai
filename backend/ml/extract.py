"""Turn an uploaded file into text.

Most onboarding documents are digital PDFs with a real text layer, which is both
faster and far more accurate than OCR. OCR is therefore a fallback for scans and
photos, and is an optional dependency: if no OCR engine is installed the
pipeline still runs and simply reports that it could not read the image.
"""
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Below this many characters a PDF is treated as a scan rather than a text PDF.
MIN_TEXT_CHARS = 40


def _pdf_text(path: Path) -> str:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    chunks = []
    for page in reader.pages[:10]:
        try:
            chunks.append(page.extract_text() or "")
        except Exception:
            logger.warning("Failed to extract text from a page of %s", path.name)
    return "\n".join(chunks).strip()


def _ocr(path: Path) -> tuple[str, str]:
    try:
        import pytesseract
        from PIL import Image
        return pytesseract.image_to_string(Image.open(path)).strip(), "ocr:tesseract"
    except Exception:
        pass

    try:
        import easyocr
        reader = easyocr.Reader(["en"], gpu=False, verbose=False)
        return "\n".join(reader.readtext(str(path), detail=0)), "ocr:easyocr"
    except Exception:
        pass

    return "", "ocr:unavailable"


def extract_text(path: Path, content_type: str) -> dict:
    """Return {text, method, char_count}. Never raises on unreadable input."""
    path = Path(path)

    try:
        if content_type == "application/pdf":
            text = _pdf_text(path)
            if len(text) >= MIN_TEXT_CHARS:
                return {"text": text, "method": "pdf:text-layer", "char_count": len(text)}
            scanned, method = _ocr(path)
            if scanned:
                return {"text": scanned, "method": f"pdf:{method}", "char_count": len(scanned)}
            return {
                "text": text,
                "method": "pdf:no-text-layer",
                "char_count": len(text),
                "note": "PDF appears to be a scan and no OCR engine is installed.",
            }

        text, method = _ocr(path)
        note = None if text else "No OCR engine installed; install pytesseract or easyocr."
        return {"text": text, "method": method, "char_count": len(text), "note": note}

    except Exception as exc:
        logger.exception("Text extraction failed for %s", path)
        return {"text": "", "method": "error", "char_count": 0, "note": f"{type(exc).__name__}: {exc}"}
