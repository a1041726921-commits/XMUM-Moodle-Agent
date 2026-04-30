# XMUM Moodle Agent Design

## Goal

Build a local Python agent that logs in to XMUM Moodle with Campus ID credentials, downloads new course materials every day, organizes them by course, and updates a bilingual Word knowledge checklist.

## Authentication

The agent uses Playwright to open `https://l.xmu.edu.my/my/`, fills the Moodle login form, and reads credentials only from environment variables or a local `.env` file:

- `XMUM_MOODLE_USERNAME`
- `XMUM_MOODLE_PASSWORD`
- `XMUM_COURSE_INCLUDE_REGEX` defaults to `2026/04` so only current-semester courses are processed.
- `XMUM_COURSE_EXCLUDE_REGEX` optionally removes matching courses after the include filter.

Credentials are not written to logs, indexes, filenames, or generated documents.

## Data Layout

Downloaded course files live under `data/courses/<course-name>/`. The agent maintains `data/index.json` to track source URLs, local paths, content hashes, course names, discovered lecture titles, and processing status. The generated document is `data/XMUM_Knowledge_Checklist.docx`.

## Workflow

1. Load configuration and credentials.
2. Log in to Moodle and open the user's course dashboard.
3. Discover course links from `my/`.
4. Filter discovered courses by the configured include/exclude regular expressions.
5. Visit each course and collect downloadable resources such as PDF, PPTX, DOCX, PPT, and ZIP files.
6. Download only new or changed resources.
7. Parse supported files locally.
8. Generate professor-style bilingual notes from the extracted text.
9. Rebuild the Word knowledge checklist from indexed parsed content.
10. Optionally register a Windows Task Scheduler job for daily 08:00 execution.

## Knowledge Checklist Shape

The Word document contains a cover section, update metadata, one section per course, and one section per lecture/resource. Each lecture section includes:

- Lecture title / 讲座标题
- Subtopics / 小标题
- Professor-style explanation / 教授式讲解
- Core concepts / 核心概念, shown in Chinese and English
- Key takeaways / 重点总结
- Review questions / 复习问题
- Source file / 来源文件

## Error Handling

The agent fails fast when credentials are missing. Download failures are recorded in the run log but do not stop other courses. Unsupported files remain downloaded and indexed, but are marked as unparsed. If Moodle selectors change, the Playwright module raises a clear login or discovery error.

## Testing Strategy

Local deterministic modules are covered with unit tests: configuration loading, index behavior, filename sanitization, parser fallbacks, knowledge note generation, and DOCX creation. Moodle browser automation is isolated behind a module boundary so it can be tested manually with real credentials without exposing secrets.
