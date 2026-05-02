import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from xmum_moodle_downloader.moodle import (
    MoodleClient,
    _course_overview_urls,
    configure_playwright_browser_path,
    discover_courses_from_links,
    discover_resources_from_links,
)


class MoodleDiscoveryTests(unittest.TestCase):
    def test_discovers_courses_from_moodle_course_links(self):
        links = [
            ("Artificial Intelligence", "https://l.xmu.edu.my/course/view.php?id=123"),
            ("Calendar", "https://l.xmu.edu.my/calendar/view.php"),
            ("Artificial Intelligence", "https://l.xmu.edu.my/course/view.php?id=123"),
        ]

        courses = discover_courses_from_links(links)

        self.assertEqual(len(courses), 1)
        self.assertEqual(courses[0].title, "Artificial Intelligence")

    def test_duplicate_course_link_keeps_better_card_title(self):
        links = [
            ("Course image", "https://l.xmu.edu.my/course/view.php?id=12583"),
            (
                "Course name\nCYS201 Modern Cryptography 2026/04 Iftekhar ...",
                "https://l.xmu.edu.my/course/view.php?id=12583",
            ),
        ]

        courses = discover_courses_from_links(links)

        self.assertEqual(len(courses), 1)
        self.assertEqual(courses[0].title, "CYS201 Modern Cryptography 2026/04 Iftekhar ...")

    def test_duplicate_course_link_replaces_course_category_image_title(self):
        links = [
            ("Course category 2025 - 2026 Course image", "https://l.xmu.edu.my/course/view.php?id=12583"),
            (
                "CYS201 Modern Cryptography 2026/04 Iftekhar Salam & Yau Wei-Chuen",
                "https://l.xmu.edu.my/course/view.php?id=12583",
            ),
        ]

        courses = discover_courses_from_links(links)

        self.assertEqual(
            courses[0].title,
            "CYS201 Modern Cryptography 2026/04 Iftekhar Salam & Yau Wei-Chuen",
        )

    def test_course_title_prefers_actions_for_course_full_name(self):
        links = [
            (
                "Course image\nCourse name\nCYS201 Modern Cryptography 2026/04 Iftekhar ...\n"
                "Actions for course CYS201 Modern Cryptography 2026/04 Iftekhar Salam & Yau Wei-Chuen",
                "https://l.xmu.edu.my/course/view.php?id=12583",
            ),
        ]

        courses = discover_courses_from_links(links)

        self.assertEqual(
            courses[0].title,
            "CYS201 Modern Cryptography 2026/04 Iftekhar Salam & Yau Wei-Chuen",
        )

    def test_discovers_downloadable_resources_from_pluginfile_and_resource_links(self):
        links = [
            ("Lecture 01 Slides", "https://l.xmu.edu.my/pluginfile.php/123/mod_resource/content/1/Lecture01.pdf"),
            ("Lecture 02", "https://l.xmu.edu.my/mod/resource/view.php?id=456"),
            ("Forum", "https://l.xmu.edu.my/mod/forum/view.php?id=789"),
        ]

        resources = discover_resources_from_links("Artificial Intelligence", links)

        self.assertEqual(len(resources), 2)
        self.assertEqual(resources[0].extension, ".pdf")
        self.assertEqual(resources[1].title, "Lecture 02")

    def test_duplicate_resource_link_keeps_better_activity_title(self):
        links = [
            ("", "https://l.xmu.edu.my/mod/resource/view.php?id=456"),
            ("Lecture 02 文件", "https://l.xmu.edu.my/mod/resource/view.php?id=456"),
        ]

        resources = discover_resources_from_links("Operating Systems", links)

        self.assertEqual(len(resources), 1)
        self.assertEqual(resources[0].title, "Lecture 02")

    def test_configures_playwright_browser_cache_for_frozen_exe(self):
        with tempfile.TemporaryDirectory() as tmp:
            local_app_data = Path(tmp)
            browser_cache = local_app_data / "ms-playwright"
            browser_cache.mkdir()

            with patch.dict(os.environ, {"LOCALAPPDATA": str(local_app_data)}, clear=True):
                configure_playwright_browser_path(frozen=True)
                self.assertEqual(os.environ["PLAYWRIGHT_BROWSERS_PATH"], str(browser_cache))

    def test_keeps_explicit_playwright_browser_path(self):
        with patch.dict(os.environ, {"PLAYWRIGHT_BROWSERS_PATH": "D:\\Browsers"}, clear=True):
            configure_playwright_browser_path(frozen=True)

            self.assertEqual(os.environ["PLAYWRIGHT_BROWSERS_PATH"], "D:\\Browsers")

    def test_frozen_exe_overrides_pyinstaller_temp_playwright_browser_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            local_app_data = Path(tmp) / "LocalAppData"
            browser_cache = local_app_data / "ms-playwright"
            browser_cache.mkdir(parents=True)
            bundled_path = Path(tmp) / "_MEI12345" / "playwright" / "driver" / "package" / ".local-browsers"

            with patch.dict(
                os.environ,
                {
                    "LOCALAPPDATA": str(local_app_data),
                    "PLAYWRIGHT_BROWSERS_PATH": str(bundled_path),
                },
                clear=True,
            ):
                configure_playwright_browser_path(frozen=True)

                self.assertEqual(os.environ["PLAYWRIGHT_BROWSERS_PATH"], str(browser_cache))

    def test_course_overview_urls_prioritize_my_courses_page(self):
        urls = _course_overview_urls("https://l.xmu.edu.my/my/")

        self.assertEqual(urls[0], "https://l.xmu.edu.my/my/courses.php")
        self.assertIn("https://l.xmu.edu.my/my/", urls)


class AsyncMoodleDiscoveryTests(unittest.IsolatedAsyncioTestCase):
    async def test_discover_courses_waits_for_async_course_links(self):
        class FakePage:
            def __init__(self):
                self.network_idle = False

            async def goto(self, url, wait_until):
                self.url = url

            async def wait_for_load_state(self, state, timeout=10000):
                if state == "networkidle":
                    self.network_idle = True

            async def eval_on_selector_all(self, selector, script):
                if not self.network_idle:
                    return []
                return [
                    [
                        "Artificial Intelligence",
                        "https://l.xmu.edu.my/course/view.php?id=123",
                    ]
                ]

        client = MoodleClient(config=type("Config", (), {"moodle_courses_url": "https://l.xmu.edu.my/my/"})())
        client.page = FakePage()

        courses = await client.discover_courses()

        self.assertEqual(len(courses), 1)
        self.assertEqual(courses[0].title, "Artificial Intelligence")

    async def test_discover_courses_merges_my_and_my_courses_pages(self):
        class FakePage:
            def __init__(self):
                self.current_url = ""

            async def goto(self, url, wait_until):
                self.current_url = url

            async def wait_for_load_state(self, state, timeout=10000):
                pass

            async def eval_on_selector_all(self, selector, script):
                if self.current_url.endswith("/my/"):
                    return [
                        [
                            "CYS202 Principles of Operating Systems 2026/04 Venantius",
                            "https://l.xmu.edu.my/course/view.php?id=13051",
                        ]
                    ]
                return [
                    [
                        "CYS201 Modern Cryptography 2026/04 Iftekhar",
                        "https://l.xmu.edu.my/course/view.php?id=12583",
                    ]
                ]

        client = MoodleClient(config=type("Config", (), {"moodle_courses_url": "https://l.xmu.edu.my/my/"})())
        client.page = FakePage()

        courses = await client.discover_courses()

        self.assertEqual([course.title for course in courses], [
            "CYS201 Modern Cryptography 2026/04 Iftekhar",
            "CYS202 Principles of Operating Systems 2026/04 Venantius",
        ])

    async def test_discover_courses_selects_all_courses_and_expands_hidden_course_cards(self):
        class FakeLocator:
            def __init__(self, page, selector):
                self.page = page
                self.selector = selector

            @property
            def first(self):
                return self

            async def count(self):
                if "Show more" in self.selector and not self.page.expanded:
                    return 1
                return 0

            async def click(self):
                if "Show more" in self.selector:
                    self.page.expanded = True

        class FakePage:
            def __init__(self):
                self.current_url = ""
                self.all_courses_requested = False
                self.expanded = False

            async def goto(self, url, wait_until):
                self.current_url = url

            async def wait_for_load_state(self, state, timeout=10000):
                pass

            async def evaluate(self, script):
                if "allincludinghidden" in script and "including removed from view" in script:
                    self.all_courses_requested = True
                return True

            def locator(self, selector):
                return FakeLocator(self, selector)

            async def eval_on_selector_all(self, selector, script):
                links = [
                    [
                        "CYS202 Principles of Operating Systems 2026/04 Venantius",
                        "https://l.xmu.edu.my/course/view.php?id=13051",
                    ]
                ]
                if self.current_url.endswith("/my/courses.php") and self.all_courses_requested and self.expanded:
                    links.append(
                        [
                            "CST101 Software Engineering 2025/09 Lecturer",
                            "https://l.xmu.edu.my/course/view.php?id=12001",
                        ]
                    )
                return links

        client = MoodleClient(config=type("Config", (), {"moodle_courses_url": "https://l.xmu.edu.my/my/"})())
        client.page = FakePage()

        courses = await client.discover_courses()

        self.assertEqual([course.title for course in courses], [
            "CYS202 Principles of Operating Systems 2026/04 Venantius",
            "CST101 Software Engineering 2025/09 Lecturer",
        ])


if __name__ == "__main__":
    unittest.main()
