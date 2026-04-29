import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from xmum_moodle_agent.docx_writer import write_knowledge_docx
from xmum_moodle_agent.knowledge import LectureNote


class DocxWriterTests(unittest.TestCase):
    def test_write_knowledge_docx_contains_course_and_lecture_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "knowledge.docx"
            notes_by_course = {
                "Machine Learning": [
                    LectureNote(
                        title="Lecture 01: Introduction",
                        subtopics=["Learning Paradigms"],
                        professor_explanation="From a professor's perspective, this lecture frames the field.",
                        core_concepts=["核心概念 Core Concept: Supervised Learning / 监督学习"],
                        key_takeaways=["Models learn patterns from data."],
                        review_questions=["How does supervised learning differ from unsupervised learning?"],
                        source_file="lecture01.pdf",
                    )
                ]
            }

            write_knowledge_docx(notes_by_course, output)

            with ZipFile(output) as docx_zip:
                document_xml = docx_zip.read("word/document.xml").decode("utf-8")

        self.assertIn("XMUM Moodle Knowledge Checklist", document_xml)
        self.assertIn("Machine Learning", document_xml)
        self.assertIn("Lecture 01: Introduction", document_xml)
        self.assertIn("Supervised Learning", document_xml)


if __name__ == "__main__":
    unittest.main()
