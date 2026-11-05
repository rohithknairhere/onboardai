"""Filesystem storage for employee document uploads."""
import hashlib
import re
import uuid
from pathlib import Path

STORAGE_ROOT = Path(__file__).resolve().parent / "storage"
MAX_BYTES = 10 * 1024 * 1024
CHUNK = 64 * 1024

# The declared content type is attacker-controlled, so each allowed type is
# pinned to the magic bytes a real file of that type must start with.
ALLOWED_TYPES = {
    "application/pdf": (".pdf", [b"%PDF-"]),
    "image/jpeg": (".jpg", [b"\xff\xd8\xff"]),
    "image/png": (".png", [b"\x89PNG\r\n\x1a\n"]),
}

_SAFE_ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


class UploadRejected(Exception):
    pass


def _safe_segment(value: str, label: str) -> str:
    if not _SAFE_ID.match(value or ""):
        raise UploadRejected(f"Invalid {label}.")
    return value


def sniff_type(head: bytes, declared: str | None) -> str:
    """Identify the file from its leading bytes, ignoring the declared type."""
    for mime, (_, signatures) in ALLOWED_TYPES.items():
        if any(head.startswith(sig) for sig in signatures):
            return mime
    raise UploadRejected(
        "Unsupported file type. Only PDF, JPEG and PNG files are accepted."
    )


def save_upload(file_obj, emp_id: str, declared_type: str | None) -> dict:
    """Stream an upload to disk, enforcing size and real file type.

    Returns metadata for persisting a DocumentUpload row.
    """
    emp_id = _safe_segment(emp_id, "employee id")

    head = file_obj.read(8)
    if not head:
        raise UploadRejected("File is empty.")
    content_type = sniff_type(head, declared_type)
    extension = ALLOWED_TYPES[content_type][0]

    upload_id = uuid.uuid4().hex
    target_dir = STORAGE_ROOT / emp_id
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / f"{upload_id}{extension}"

    digest = hashlib.sha256()
    size = 0

    try:
        with open(target_path, "wb") as out:
            buffer = head
            while buffer:
                size += len(buffer)
                if size > MAX_BYTES:
                    raise UploadRejected("File exceeds the 10MB limit.")
                digest.update(buffer)
                out.write(buffer)
                buffer = file_obj.read(CHUNK)
    except Exception:
        target_path.unlink(missing_ok=True)
        raise

    return {
        "id": upload_id,
        "stored_path": str(target_path.relative_to(STORAGE_ROOT)),
        "content_type": content_type,
        "size_bytes": size,
        "sha256": digest.hexdigest(),
    }


def resolve(stored_path: str) -> Path:
    """Turn a stored relative path back into an absolute one, refusing escapes."""
    candidate = (STORAGE_ROOT / stored_path).resolve()
    if not candidate.is_relative_to(STORAGE_ROOT.resolve()):
        raise UploadRejected("Invalid stored path.")
    return candidate
