from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True)
class Course:
    title: str
    url: str


@dataclass(frozen=True)
class Resource:
    title: str
    url: str
    course_title: str
    extension: str = ""


@dataclass
class ParsedMaterial:
    title: str
    headings: List[str]
    text: str
    source_file: str
    parser: str = "unknown"


@dataclass
class LectureNote:
    title: str
    subtopics: List[str]
    professor_explanation: str
    core_concepts: List[str]
    key_takeaways: List[str]
    review_questions: List[str]
    source_file: str


@dataclass
class MaterialRecord:
    url: str
    course_title: str
    resource_title: str
    local_path: str
    sha256: str
    extension: str
    downloaded_at: str = field(default_factory=utc_now_iso)
    parsed_at: Optional[str] = None
    parsed_title: Optional[str] = None
    headings: List[str] = field(default_factory=list)
    text_excerpt: str = ""
    parser: str = "unknown"

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "MaterialRecord":
        return cls(
            url=str(data["url"]),
            course_title=str(data["course_title"]),
            resource_title=str(data["resource_title"]),
            local_path=str(data["local_path"]),
            sha256=str(data["sha256"]),
            extension=str(data.get("extension", "")),
            downloaded_at=str(data.get("downloaded_at") or utc_now_iso()),
            parsed_at=data.get("parsed_at") if data.get("parsed_at") else None,
            parsed_title=data.get("parsed_title") if data.get("parsed_title") else None,
            headings=list(data.get("headings") or []),
            text_excerpt=str(data.get("text_excerpt") or ""),
            parser=str(data.get("parser") or "unknown"),
        )

    @property
    def path(self) -> Path:
        return Path(self.local_path)
