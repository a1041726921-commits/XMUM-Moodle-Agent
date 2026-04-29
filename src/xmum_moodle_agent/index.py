import json
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from .models import MaterialRecord, ParsedMaterial, Resource, utc_now_iso


class MaterialIndex:
    def __init__(self, path: Path):
        self.path = path
        self.records: List[MaterialRecord] = []
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            self.records = []
            return
        data = json.loads(self.path.read_text(encoding="utf-8"))
        self.records = [MaterialRecord.from_dict(item) for item in data.get("records", [])]

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"records": [record.to_dict() for record in self.records]}
        self.path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def by_url(self, url: str) -> Optional[MaterialRecord]:
        for record in self.records:
            if record.url == url:
                return record
        return None

    def upsert_downloaded(
        self,
        resource: Resource,
        local_path: Path,
        sha256: str,
        text_excerpt: str = "",
    ) -> bool:
        existing = self.by_url(resource.url)
        if existing and existing.sha256 == sha256:
            return False

        if existing:
            existing.course_title = resource.course_title
            existing.resource_title = resource.title
            existing.local_path = str(local_path)
            existing.sha256 = sha256
            existing.extension = resource.extension
            existing.downloaded_at = utc_now_iso()
            existing.text_excerpt = text_excerpt
            return True

        self.records.append(
            MaterialRecord(
                url=resource.url,
                course_title=resource.course_title,
                resource_title=resource.title,
                local_path=str(local_path),
                sha256=sha256,
                extension=resource.extension,
                text_excerpt=text_excerpt,
            )
        )
        return True

    def mark_parsed(self, record: MaterialRecord, parsed: ParsedMaterial) -> None:
        record.parsed_at = utc_now_iso()
        record.parsed_title = parsed.title
        record.headings = parsed.headings
        record.text_excerpt = parsed.text[:5000]
        record.parser = parsed.parser

    def grouped_by_course(self) -> Dict[str, List[MaterialRecord]]:
        grouped: Dict[str, List[MaterialRecord]] = {}
        for record in self.records:
            grouped.setdefault(record.course_title, []).append(record)
        for records in grouped.values():
            records.sort(key=lambda item: (item.resource_title.lower(), item.local_path.lower()))
        return dict(sorted(grouped.items(), key=lambda item: item[0].lower()))

    def __iter__(self) -> Iterable[MaterialRecord]:
        return iter(self.records)
