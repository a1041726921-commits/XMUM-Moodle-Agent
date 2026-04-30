import unittest

from xmum_moodle_agent.moodle import MoodleClient, discover_courses_from_links, discover_resources_from_links


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
            "CYS202 Principles of Operating Systems 2026/04 Venantius",
            "CYS201 Modern Cryptography 2026/04 Iftekhar",
        ])


if __name__ == "__main__":
    unittest.main()
