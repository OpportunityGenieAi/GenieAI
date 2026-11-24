"""Pure helpers for the consultation feature (no database or network)."""
import base64
import binascii
import os
import re
from typing import Optional, Tuple

MAX_FILE_BYTES = 5 * 1024 * 1024
MAX_FILES = 3

# product id -> minutes (ids can be overridden with env vars)
PRODUCT_30 = os.environ.get("CONSULT_PRODUCT_30", "consult_30min")
PRODUCT_60 = os.environ.get("CONSULT_PRODUCT_60", "consult_60min")
PRODUCTS = {PRODUCT_30: 30, PRODUCT_60: 60}

_ALLOWED = {
    "pdf": "application/pdf",
    "doc": "application/msword",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "txt": "text/plain",
    "rtf": "application/rtf",
    "odt": "application/vnd.oasis.opendocument.text",
}


def safe_filename(name: str) -> str:
    name = os.path.basename((name or "").replace("\\", "/")).strip()
    name = re.sub(r"[^A-Za-z0-9._ \-()]", "_", name)[:120].strip(" .")
    return name or "document"


def extension(name: str) -> str:
    return name.rsplit(".", 1)[-1].lower() if "." in name else ""


def sniff_ok(ext: str, data: bytes) -> bool:
    """Checks that the file's first bytes match what its extension claims."""
    if ext == "pdf":
        return data[:5] == b"%PDF-"
    if ext in ("docx", "odt"):
        return data[:4] == b"PK\x03\x04"
    if ext == "doc":
        return data[:8] == bytes.fromhex("D0CF11E0A1B11AE1")
    if ext == "rtf":
        return data[:5] == b"{\\rtf"
    if ext == "txt":
        return b"\x00" not in data[:4096]
    return False


def decode_upload(filename: str, b64: str) -> Tuple[Optional[Tuple[str, str, bytes]], Optional[str]]:
    """Returns ((clean name, content type, bytes), None) or (None, error message)."""
    name = safe_filename(filename)
    ext = extension(name)
    if ext not in _ALLOWED:
        return None, "Please attach a PDF, Word (.doc/.docx), .txt, .rtf or .odt file."
    try:
        data = base64.b64decode((b64 or "").split(",")[-1], validate=False)
    except (binascii.Error, ValueError):
        return None, "That file couldn't be read."
    if not data:
        return None, "That file is empty."
    if len(data) > MAX_FILE_BYTES:
        return None, "Each file must be 5 MB or smaller."
    if not sniff_ok(ext, data):
        return None, f"That doesn't look like a real .{ext} file."
    return (name, _ALLOWED[ext], data), None


def clean(value: Optional[str], limit: int) -> str:
    return re.sub(r"[ \t]+", " ", (value or "").replace("\r", "")).strip()[:limit]


def valid_email(value: str) -> bool:
    return bool(re.fullmatch(r"[^@\s]{1,64}@[^@\s]+\.[^@\s]{2,}", value or "")) and len(value) <= 254
