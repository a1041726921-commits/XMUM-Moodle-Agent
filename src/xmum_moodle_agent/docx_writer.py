import html
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List

from .models import LectureNote


def write_knowledge_docx(notes_by_course: Dict[str, List[LectureNote]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    document_xml = _document_xml(notes_by_course)
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as docx:
        docx.writestr("[Content_Types].xml", _content_types_xml())
        docx.writestr("_rels/.rels", _rels_xml())
        docx.writestr("word/_rels/document.xml.rels", _document_rels_xml())
        docx.writestr("word/styles.xml", _styles_xml())
        docx.writestr("word/document.xml", document_xml)


def _document_xml(notes_by_course: Dict[str, List[LectureNote]]) -> str:
    body: List[str] = []
    body.append(_p("XMUM Moodle Knowledge Checklist", style="Title"))
    body.append(_p(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"))
    body.append(_p("Automatically generated from downloaded XMUM Moodle course materials."))

    for course_title, notes in notes_by_course.items():
        body.append(_p(course_title, style="Heading1"))
        for note in notes:
            body.extend(_note_blocks(note))

    body.append(
        '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" w:header="708" w:footer="708" w:gutter="0"/></w:sectPr>'
    )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body>{''.join(body)}</w:body></w:document>"
    )


def _note_blocks(note: LectureNote) -> Iterable[str]:
    blocks: List[str] = [_p(note.title, style="Heading2")]
    blocks.append(_p("Subtopics / 小标题", style="Heading3"))
    blocks.extend(_bullet(item) for item in note.subtopics)
    blocks.append(_p("Professor-style Explanation / 教授式讲解", style="Heading3"))
    blocks.append(_p(note.professor_explanation))
    blocks.append(_p("Core Concepts / 核心概念", style="Heading3"))
    blocks.extend(_bullet(item) for item in note.core_concepts)
    blocks.append(_p("Key Takeaways / 重点总结", style="Heading3"))
    blocks.extend(_bullet(item) for item in note.key_takeaways)
    blocks.append(_p("Review Questions / 复习问题", style="Heading3"))
    blocks.extend(_bullet(item) for item in note.review_questions)
    blocks.append(_p(f"Source file / 来源文件: {note.source_file}"))
    return blocks


def _p(text: str, style: str = "") -> str:
    style_xml = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>' if style else ""
    return f"<w:p>{style_xml}<w:r><w:t>{html.escape(text)}</w:t></w:r></w:p>"


def _bullet(text: str) -> str:
    return _p(f"- {text}")


def _content_types_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>"""


def _rels_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""


def _document_rels_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>"""


def _styles_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:style w:type="paragraph" w:styleId="Normal"><w:name w:val="Normal"/></w:style>
  <w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/><w:rPr><w:b/><w:sz w:val="40"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:rPr><w:b/><w:sz w:val="32"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/><w:rPr><w:b/><w:sz w:val="26"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="Heading3"><w:name w:val="heading 3"/><w:rPr><w:b/><w:sz w:val="22"/></w:rPr></w:style>
</w:styles>"""
