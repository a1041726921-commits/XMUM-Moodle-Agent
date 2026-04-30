import unittest

from xmum_moodle_agent.course_filter import filter_courses
from xmum_moodle_agent.models import Course


class CourseFilterTests(unittest.TestCase):
    def test_include_regex_keeps_current_term_courses(self):
        courses = [
            Course("CYS202 Principles of Operating Systems 2026/04 Venantius", "https://example.test/1"),
            Course("CST204 Data Structures 2025/04 Usman", "https://example.test/2"),
        ]

        filtered = filter_courses(courses, include_regex="2026/04", exclude_regex=None)

        self.assertEqual([course.title for course in filtered], [courses[0].title])

    def test_blank_include_regex_keeps_all_courses(self):
        courses = [
            Course("CYS202 Principles of Operating Systems 2026/04 Venantius", "https://example.test/1"),
            Course("CST204 Data Structures 2025/04 Usman", "https://example.test/2"),
        ]

        filtered = filter_courses(courses, include_regex="", exclude_regex=None)

        self.assertEqual(filtered, courses)

    def test_exclude_regex_removes_matching_courses_after_include(self):
        courses = [
            Course("CYS202 Principles of Operating Systems 2026/04 Venantius", "https://example.test/1"),
            Course("G0182 The Four Great Classical Chinese Novels 2026/04 Wang", "https://example.test/2"),
        ]

        filtered = filter_courses(courses, include_regex="2026/04", exclude_regex="^G")

        self.assertEqual([course.title for course in filtered], [courses[0].title])


if __name__ == "__main__":
    unittest.main()
