import tempfile
import unittest
from pathlib import Path

from xmum_moodle_agent.files import content_sha256, safe_filename
from xmum_moodle_agent.index import MaterialIndex
from xmum_moodle_agent.models import Course, Resource
from xmum_moodle_agent.downloader import save_resource_bytes


class IndexAndFilesTests(unittest.TestCase):
    def test_safe_filename_removes_windows_forbidden_characters(self):
        name = safe_filename('Lecture 01: Intro / "AI"?*')
        self.assertEqual(name, "Lecture 01 - Intro - AI")

    def test_content_sha256_hashes_file_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.txt"
            path.write_bytes(b"abc")
            self.assertEqual(
                content_sha256(path),
                "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
            )

    def test_index_upserts_resource_by_url_and_persists(self):
        with tempfile.TemporaryDirectory() as tmp:
            index_path = Path(tmp) / "index.json"
            index = MaterialIndex(index_path)
            course = Course(title="Machine Learning", url="https://l.xmu.edu.my/course/view.php?id=1")
            resource = Resource(
                title="Lecture 01",
                url="https://l.xmu.edu.my/pluginfile.php/1/lecture01.pdf",
                course_title=course.title,
                extension=".pdf",
            )

            changed = index.upsert_downloaded(
                resource=resource,
                local_path=Path(tmp) / "Machine Learning" / "Lecture 01.pdf",
                sha256="hash-1",
                text_excerpt="Intro text",
            )
            changed_again = index.upsert_downloaded(
                resource=resource,
                local_path=Path(tmp) / "Machine Learning" / "Lecture 01.pdf",
                sha256="hash-1",
                text_excerpt="Intro text",
            )
            index.save()

            reloaded = MaterialIndex(index_path)

        self.assertTrue(changed)
        self.assertFalse(changed_again)
        self.assertEqual(len(reloaded.records), 1)
        self.assertEqual(reloaded.records[0].course_title, "Machine Learning")

    def test_save_resource_bytes_uses_stable_path_for_same_resource(self):
        with tempfile.TemporaryDirectory() as tmp:
            courses_dir = Path(tmp) / "courses"
            resource = Resource(
                title="Lecture 01",
                url="https://l.xmu.edu.my/pluginfile.php/1/lecture01.pdf",
                course_title="Machine Learning",
                extension=".pdf",
            )

            first = save_resource_bytes(courses_dir, resource, b"first")
            second = save_resource_bytes(courses_dir, resource, b"second")
            second_content = second.read_bytes()

        self.assertEqual(first, second)
        self.assertEqual(second_content, b"second")

    def test_save_resource_bytes_groups_course_under_semester_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            courses_dir = Path(tmp) / "courses"
            resource = Resource(
                title="Lecture 01",
                url="https://l.xmu.edu.my/pluginfile.php/1/lecture01.pdf",
                course_title="Machine Learning 2025/09 Lecturer",
                extension=".pdf",
            )

            path = save_resource_bytes(courses_dir, resource, b"content")

        self.assertEqual(
            path,
            courses_dir / "2025-09" / "Machine Learning 2025 - 09 Lecturer" / "Lecture 01.pdf",
        )


if __name__ == "__main__":
    unittest.main()
