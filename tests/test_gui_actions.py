import tempfile
import unittest
from pathlib import Path

from xmum_moodle_downloader.gui_actions import (
    CourseDownloadReport,
    course_terms_from_courses,
    download_selected_courses,
    filter_courses_by_term,
    visible_courses_after_login,
)
from xmum_moodle_downloader.models import Course, Resource


class FakeMoodleClient:
    def __init__(self):
        self.login_called = False
        self.courses = [
            Course("CST101 Software Engineering", "https://moodle/course/view.php?id=1"),
            Course("MAT102 Algebra", "https://moodle/course/view.php?id=2"),
        ]
        self.resources = {
            "CST101 Software Engineering": [
                Resource(
                    "Week 1 Slides",
                    "https://moodle/pluginfile.php/1/week-1.pdf",
                    "CST101 Software Engineering",
                    ".pdf",
                ),
                Resource(
                    "Week 2 Slides",
                    "https://moodle/pluginfile.php/1/week-2.pdf",
                    "CST101 Software Engineering",
                    ".pdf",
                ),
            ],
            "MAT102 Algebra": [
                Resource("Formula Sheet", "https://moodle/pluginfile.php/2/formula.pdf", "MAT102 Algebra", ".pdf")
            ],
        }

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    async def login(self):
        self.login_called = True

    async def discover_courses(self):
        return self.courses

    async def discover_resources(self, course):
        return self.resources[course.title]

    async def download_resource_bytes(self, resource):
        return f"content for {resource.title}".encode("utf-8"), resource.url


class GuiActionsTests(unittest.IsolatedAsyncioTestCase):
    def test_course_terms_are_sorted_with_latest_semester_first(self):
        courses = [
            Course("CYS201 Modern Cryptography 2026/04 Iftekhar", "https://moodle/course/view.php?id=1"),
            Course("CST101 Software Engineering 2025/09 Lecturer", "https://moodle/course/view.php?id=2"),
            Course("General Moodle Orientation", "https://moodle/course/view.php?id=3"),
            Course("CYS202 Operating Systems 2026/04 Venantius", "https://moodle/course/view.php?id=4"),
        ]

        terms = course_terms_from_courses(courses)

        self.assertEqual(terms, ["2026/04", "2025/09"])

    def test_filter_courses_by_selected_semester(self):
        courses = [
            Course("CYS201 Modern Cryptography 2026/04 Iftekhar", "https://moodle/course/view.php?id=1"),
            Course("CST101 Software Engineering 2025/09 Lecturer", "https://moodle/course/view.php?id=2"),
            Course("General Moodle Orientation", "https://moodle/course/view.php?id=3"),
        ]

        filtered = filter_courses_by_term(courses, "2025/09")

        self.assertEqual([course.title for course in filtered], ["CST101 Software Engineering 2025/09 Lecturer"])

    def test_filter_courses_without_semester_keeps_all_courses(self):
        courses = [
            Course("CYS201 Modern Cryptography 2026/04 Iftekhar", "https://moodle/course/view.php?id=1"),
            Course("General Moodle Orientation", "https://moodle/course/view.php?id=3"),
        ]

        filtered = filter_courses_by_term(courses, "")

        self.assertEqual(filtered, courses)

    async def test_visible_courses_after_login_logs_in_and_returns_courses(self):
        fake = FakeMoodleClient()

        courses = await visible_courses_after_login(fake)

        self.assertTrue(fake.login_called)
        self.assertEqual([course.title for course in courses], ["CST101 Software Engineering", "MAT102 Algebra"])

    async def test_download_selected_courses_skips_existing_indexed_resources(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fake = FakeMoodleClient()
            report = await download_selected_courses(root, fake, [fake.courses[0]])
            second_report = await download_selected_courses(root, fake, [fake.courses[0]])

        self.assertEqual(report, CourseDownloadReport(courses=1, resources=2, downloaded=2, skipped=0))
        self.assertEqual(second_report, CourseDownloadReport(courses=1, resources=2, downloaded=0, skipped=2))

    async def test_download_selected_courses_does_not_overwrite_existing_same_name_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            existing = root / "data" / "courses" / "2026-04" / "CST101 Software Engineering 2026 - 04" / "Week 1 Slides.pdf"
            existing.parent.mkdir(parents=True)
            existing.write_text("human file", encoding="utf-8")
            fake = FakeMoodleClient()
            fake.courses[0] = Course("CST101 Software Engineering 2026/04", fake.courses[0].url)
            fake.resources["CST101 Software Engineering 2026/04"] = fake.resources.pop("CST101 Software Engineering")

            report = await download_selected_courses(root, fake, [fake.courses[0]])

            original_text = existing.read_text(encoding="utf-8")
            new_files = sorted(path.name for path in existing.parent.glob("Week 1 Slides*.pdf"))

        self.assertEqual(report.downloaded, 2)
        self.assertEqual(original_text, "human file")
        self.assertIn("Week 1 Slides (1).pdf", new_files)

    async def test_download_selected_courses_groups_course_files_by_semester(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fake = FakeMoodleClient()
            course = Course("CST101 Software Engineering 2025/09 Lecturer", fake.courses[0].url)
            fake.resources[course.title] = fake.resources[fake.courses[0].title]

            await download_selected_courses(root, fake, [course])

            expected = root / "data" / "courses" / "2025-09" / "CST101 Software Engineering 2025 - 09 Lecturer"

            self.assertTrue((expected / "Week 1 Slides.pdf").exists())


if __name__ == "__main__":
    unittest.main()
