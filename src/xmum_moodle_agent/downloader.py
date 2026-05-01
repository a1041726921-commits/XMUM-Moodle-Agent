from pathlib import Path
import re
from typing import Tuple

from .files import safe_filename
from .models import Resource
from .moodle import _extension_from_url


def target_path_for_resource(courses_dir: Path, resource: Resource, final_url: str = "") -> Path:
    course_dir = courses_dir / _term_folder(resource.course_title) / safe_filename(resource.course_title)
    extension = resource.extension or _extension_from_url(final_url) or ".bin"
    title = safe_filename(resource.title)
    if title.lower().endswith(extension.lower()):
        filename = title
    else:
        filename = f"{title}{extension}"
    return course_dir / filename


def _term_folder(course_title: str) -> str:
    match = re.search(r"\b(20\d{2})/(\d{2})\b", course_title)
    if not match:
        return "unknown-term"
    return f"{match.group(1)}-{match.group(2)}"


def save_resource_bytes(courses_dir: Path, resource: Resource, content: bytes, final_url: str = "") -> Path:
    path = target_path_for_resource(courses_dir, resource, final_url=final_url)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path
