import hashlib
import re
from pathlib import Path

WINDOWS_FORBIDDEN = r'[<>:"/\\|?*\x00-\x1f]'


def safe_filename(value: str, max_length: int = 150) -> str:
    cleaned = re.sub(WINDOWS_FORBIDDEN, " - ", value)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .-_")
    cleaned = re.sub(r"\s+-\s+(?:-\s+)+", " - ", cleaned)
    cleaned = re.sub(r"( - ){2,}", " - ", cleaned)
    if not cleaned:
        cleaned = "untitled"
    return cleaned[:max_length].rstrip(" .-_")


def content_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ensure_unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    counter = 2
    while True:
        candidate = parent / f"{stem} ({counter}){suffix}"
        if not candidate.exists():
            return candidate
        counter += 1
