import re
import zipfile
from html import unescape
from pathlib import Path
from typing import List
from xml.etree import ElementTree

from .models import ParsedMaterial


SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf", ".docx", ".pptx"}


def parse_material(path: Path) -> ParsedMaterial:
    extension = path.suffix.lower()
    if extension in {".txt", ".md"}:
        text = path.read_text(encoding="utf-8", errors="ignore")
        parser = "text"
    elif extension == ".pdf":
        text = _extract_pdf(path)
        parser = "pdf"
    elif extension == ".docx":
        text = _extract_docx(path)
        parser = "docx"
    elif extension == ".pptx":
        text = _extract_pptx(path)
        parser = "pptx"
    else:
        text = ""
        parser = "unsupported"

    text = _normalize_text(text)
    title = _guess_title(text, path)
    headings = _guess_headings(text, title)
    return ParsedMaterial(title=title, headings=headings, text=text, source_file=str(path), parser=parser)


def _extract_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except Exception:
        return ""

    parts: List[str] = []
    try:
        reader = PdfReader(str(path))
        for page in reader.pages:
            parts.append(page.extract_text() or "")
    except Exception:
        return ""
    return "\n".join(parts)


def _extract_docx(path: Path) -> str:
    try:
        with zipfile.ZipFile(path) as archive:
            xml = archive.read("word/document.xml")
    except Exception:
        return ""
    return _text_from_ooxml(xml)


def _extract_pptx(path: Path) -> str:
    parts: List[str] = []
    try:
        with zipfile.ZipFile(path) as archive:
            slide_names = sorted(
                name
                for name in archive.namelist()
                if name.startswith("ppt/slides/slide") and name.endswith(".xml")
            )
            for slide_name in slide_names:
                parts.append(_text_from_ooxml(archive.read(slide_name)))
    except Exception:
        return ""
    return "\n\n".join(parts)


def _text_from_ooxml(xml_bytes: bytes) -> str:
    try:
        root = ElementTree.fromstring(xml_bytes)
    except ElementTree.ParseError:
        return ""
    texts = []
    for node in root.iter():
        if node.tag.endswith("}t") and node.text:
            texts.append(node.text)
    return "\n".join(texts)


def _normalize_text(text: str) -> str:
    text = unescape(text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _guess_title(text: str, path: Path) -> str:
    for line in text.splitlines():
        line = line.strip()
        if len(line) >= 4:
            return line[:160]
    return path.stem


def _guess_headings(text: str, title: str) -> List[str]:
    headings: List[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line == title:
            continue
        word_count = len(line.split())
        looks_like_heading = (
            2 <= word_count <= 10
            and len(line) <= 90
            and not line.endswith(".")
        )
        if looks_like_heading and line not in headings:
            headings.append(line)
        if len(headings) >= 12:
            break
    return headings
