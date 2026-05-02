import tempfile
import unittest
from pathlib import Path

from xmum_moodle_downloader.parser import parse_material


class ParserTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
