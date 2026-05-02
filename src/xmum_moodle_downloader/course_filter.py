import re
from typing import Iterable, List, Optional

from .models import Course


def filter_courses(
    courses: Iterable[Course],
    include_regex: Optional[str],
    exclude_regex: Optional[str],
) -> List[Course]:
    include_pattern = re.compile(include_regex, re.IGNORECASE) if include_regex else None
    exclude_pattern = re.compile(exclude_regex, re.IGNORECASE) if exclude_regex else None
    filtered: List[Course] = []
    for course in courses:
        if include_pattern and not include_pattern.search(course.title):
            continue
        if exclude_pattern and exclude_pattern.search(course.title):
            continue
        filtered.append(course)
    return filtered
