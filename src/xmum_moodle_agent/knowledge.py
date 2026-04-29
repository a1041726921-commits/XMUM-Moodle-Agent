import re
from typing import List

from .models import LectureNote


def build_lecture_note(title: str, headings: List[str], text: str, source_file: str) -> LectureNote:
    subtopics = headings[:10] or _fallback_subtopics(text)
    sentences = _sentences(text)
    explanation = _professor_explanation(title, subtopics, sentences)
    core_concepts = _core_concepts(subtopics, sentences)
    key_takeaways = _key_takeaways(sentences)
    review_questions = _review_questions(subtopics, title)
    return LectureNote(
        title=title,
        subtopics=subtopics,
        professor_explanation=explanation,
        core_concepts=core_concepts,
        key_takeaways=key_takeaways,
        review_questions=review_questions,
        source_file=source_file,
    )


def _sentences(text: str) -> List[str]:
    chunks = re.split(r"(?<=[.!?。！？])\s+", text.replace("\n", " "))
    return [chunk.strip() for chunk in chunks if len(chunk.strip()) > 20][:12]


def _fallback_subtopics(text: str) -> List[str]:
    words = re.findall(r"[A-Za-z][A-Za-z0-9-]{3,}", text)
    seen = []
    for word in words:
        clean = word.strip("-")
        if clean.lower() not in {item.lower() for item in seen}:
            seen.append(clean)
        if len(seen) >= 5:
            break
    return seen or ["Main Ideas"]


def _professor_explanation(title: str, subtopics: List[str], sentences: List[str]) -> str:
    topic_text = ", ".join(subtopics[:4]) if subtopics else "the main ideas"
    evidence = " ".join(sentences[:4])
    if not evidence:
        evidence = "The source file did not expose enough machine-readable text, so this section should be reviewed against the original slides."
    return (
        f"From a professor's perspective, {title} should be read as a structured lecture about {topic_text}. "
        f"The important move is to connect definitions, mechanisms, and examples rather than memorizing isolated terms. "
        f"{evidence}"
    )


def _core_concepts(subtopics: List[str], sentences: List[str]) -> List[str]:
    concepts = []
    for topic in subtopics[:8]:
        concepts.append(f"核心概念 Core Concept: {topic} / {topic}")
    if not concepts and sentences:
        concepts.append(f"核心概念 Core Concept: Main argument / 主要论点")
    return concepts


def _key_takeaways(sentences: List[str]) -> List[str]:
    if not sentences:
        return ["Review the original file because extractable text was limited."]
    return sentences[:5]


def _review_questions(subtopics: List[str], title: str) -> List[str]:
    questions = [
        f"What problem is {title} trying to help us understand?",
        "Which assumptions or definitions are essential before solving related problems?",
    ]
    for topic in subtopics[:3]:
        questions.append(f"How would you explain {topic} to a classmate using one concrete example?")
    return questions
