from dataclasses import dataclass
from pathlib import Path
import re
from typing import Iterable, List

from .downloader import target_path_for_resource
from .files import content_sha256
from .index import MaterialIndex
from .models import Course, Resource


@dataclass(frozen=True)
class CourseDownloadReport:
    courses: int = 0
    resources: int = 0
    downloaded: int = 0
    skipped: int = 0


def course_terms_from_courses(courses: Iterable[Course]) -> List[str]:
    terms = {_course_term(course.title) for course in courses}
    return sorted((term for term in terms if term), reverse=True)


def filter_courses_by_term(courses: Iterable[Course], term: str) -> List[Course]:
    course_list = list(courses)
    if not term:
        return course_list
    return [course for course in course_list if _course_term(course.title) == term]


def course_term_folder(course: Course) -> str:
    term = _course_term(course.title)
    return term.replace("/", "-") if term else "unknown-term"


def _course_term(title: str) -> str:
    match = re.search(r"\b(20\d{2}/\d{2})\b", title)
    return match.group(1) if match else ""


async def visible_courses_after_login(moodle_client) -> List[Course]:
    await moodle_client.login()
    return await moodle_client.discover_courses()


async def download_selected_courses(root: Path, moodle_client, selected_courses: Iterable[Course]) -> CourseDownloadReport:
    root = root.resolve()
    data_dir = root / "data"
    courses_dir = data_dir / "courses"
    index = MaterialIndex(data_dir / "index.json")

    courses = list(selected_courses)
    resources_count = 0
    downloaded_count = 0
    skipped_count = 0

    for course in courses:
        resources = await moodle_client.discover_resources(course)
        resources_count += len(resources)
        for resource in resources:
            resource = Resource(
                title=resource.title,
                url=resource.url,
                course_title=course.title,
                extension=resource.extension,
            )
            existing = index.by_url(resource.url)
            if existing and Path(existing.local_path).exists():
                skipped_count += 1
                continue

            content, final_url = await moodle_client.download_resource_bytes(resource)
            path = _non_overwriting_path(target_path_for_resource(courses_dir, resource, final_url=final_url))
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
            sha256 = content_sha256(path)
            index.upsert_downloaded(resource, path, sha256)
            downloaded_count += 1

    index.save()
    return CourseDownloadReport(
        courses=len(courses),
        resources=resources_count,
        downloaded=downloaded_count,
        skipped=skipped_count,
    )


def _non_overwriting_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    counter = 1
    while True:
        candidate = parent / f"{stem} ({counter}){suffix}"
        if not candidate.exists():
            return candidate
        counter += 1
