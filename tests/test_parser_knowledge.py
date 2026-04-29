import tempfile
import unittest
from pathlib import Path

from xmum_moodle_agent.knowledge import build_lecture_note
from xmum_moodle_agent.parser import parse_material


class ParserKnowledgeTests(unittest.TestCase):
    def test_parse_txt_material_extracts_title_headings_and_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "lecture.txt"
            path.write_text(
                "Lecture 01: Introduction to Algorithms\n\n"
                "Sorting Algorithms\n"
                "Sorting is the process of arranging data in order.\n\n"
                "Complexity Analysis\n"
                "Big O notation describes growth rates.",
                encoding="utf-8",
            )

            parsed = parse_material(path)

        self.assertEqual(parsed.title, "Lecture 01: Introduction to Algorithms")
        self.assertIn("Sorting Algorithms", parsed.headings)
        self.assertIn("Big O notation", parsed.text)

    def test_build_lecture_note_creates_bilingual_professor_style_sections(self):
        note = build_lecture_note(
            title="Lecture 01: Introduction to Algorithms",
            headings=["Sorting Algorithms", "Complexity Analysis"],
            text=(
                "Sorting is the process of arranging data in order. "
                "Big O notation describes algorithmic growth rates."
            ),
            source_file="lecture.txt",
        )

        self.assertEqual(note.title, "Lecture 01: Introduction to Algorithms")
        self.assertIn("Sorting Algorithms", note.subtopics)
        self.assertTrue(note.professor_explanation.startswith("From a professor's perspective"))
        self.assertTrue(any("核心概念" in concept for concept in note.core_concepts))
        self.assertTrue(note.review_questions)


if __name__ == "__main__":
    unittest.main()
