import unittest

from xmum_moodle_agent.moodle import discover_courses_from_links, discover_resources_from_links


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


if __name__ == "__main__":
    unittest.main()
