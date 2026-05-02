import unittest
from pathlib import Path


class GuiAssetTests(unittest.TestCase):
    def test_apple_theme_and_assets_are_available(self):
        from xmum_moodle_downloader.gui_assets import (
            APPLE_THEME,
            app_icon_path,
            course_icon_path,
            enable_windows_dpi_awareness,
            ensure_icon_assets,
        )

        ensure_icon_assets()

        self.assertEqual(APPLE_THEME["app_bg"], "#f5f5f7")
        self.assertEqual(APPLE_THEME["surface"], "#ffffff")
        self.assertEqual(APPLE_THEME["primary"], "#0071e3")
        self.assertTrue(app_icon_path().exists())
        self.assertEqual(app_icon_path().suffix.lower(), ".ico")
        self.assertTrue(course_icon_path().exists())
        self.assertEqual(course_icon_path().suffix.lower(), ".png")
        self.assertIsNone(enable_windows_dpi_awareness())

    def test_pyinstaller_specs_include_app_icon(self):
        expected = "icon='src\\\\xmum_moodle_downloader\\\\assets\\\\xmum.ico'"
        spec_text = Path("XUMU-moodle-downloader.spec").read_text(encoding="utf-8")
        self.assertIn(expected, spec_text)


if __name__ == "__main__":
    unittest.main()
