from pathlib import Path
from typing import Dict, List

from .config import AgentConfig
from .course_filter import filter_courses
from .docx_writer import write_knowledge_docx
from .downloader import save_resource_bytes
from .files import content_sha256
from .index import MaterialIndex
from .knowledge import build_lecture_note
from .models import LectureNote, MaterialRecord, ParsedMaterial
from .moodle import MoodleClient
from .parser import parse_material


async def run_agent(config: AgentConfig) -> Dict[str, int]:
    config.courses_dir.mkdir(parents=True, exist_ok=True)
    index = MaterialIndex(config.index_path)
    stats = {"courses": 0, "resources": 0, "downloaded_or_changed": 0, "parsed": 0}

    async with MoodleClient(config) as moodle:
        await moodle.login()
        courses = filter_courses(
            await moodle.discover_courses(),
            include_regex=config.course_include_regex,
            exclude_regex=config.course_exclude_regex,
        )
        stats["courses"] = len(courses)
        for course in courses:
            resources = await moodle.discover_resources(course)
            stats["resources"] += len(resources)
            for resource in resources:
                content, final_url = await moodle.download_resource_bytes(resource)
                path = save_resource_bytes(config.courses_dir, resource, content, final_url=final_url)
                sha256 = content_sha256(path)
                changed = index.upsert_downloaded(resource, path, sha256)
                if changed:
                    stats["downloaded_or_changed"] += 1
                    record = index.by_url(resource.url)
                    if record:
                        parsed = parse_material(path)
                        index.mark_parsed(record, parsed)
                        stats["parsed"] += 1

    _parse_existing_unparsed(index)
    notes_by_course = _notes_from_index(index)
    write_knowledge_docx(notes_by_course, config.docx_path)
    index.save()
    return stats


def _parse_existing_unparsed(index: MaterialIndex) -> None:
    for record in index.records:
        if record.parsed_at or not Path(record.local_path).exists():
            continue
        parsed = parse_material(Path(record.local_path))
        index.mark_parsed(record, parsed)


def _notes_from_index(index: MaterialIndex) -> Dict[str, List[LectureNote]]:
    notes_by_course: Dict[str, List[LectureNote]] = {}
    for course_title, records in index.grouped_by_course().items():
        notes_by_course[course_title] = [_note_from_record(record) for record in records]
    return notes_by_course


def _note_from_record(record: MaterialRecord) -> LectureNote:
    parsed = ParsedMaterial(
        title=record.parsed_title or record.resource_title,
        headings=record.headings,
        text=record.text_excerpt,
        source_file=record.local_path,
        parser=record.parser,
    )
    return build_lecture_note(
        title=parsed.title,
        headings=parsed.headings,
        text=parsed.text,
        source_file=parsed.source_file,
    )
