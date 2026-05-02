import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from xmum_moodle_downloader.models import Course


def qt_app():
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


class QtGuiImportTests(unittest.TestCase):
    def test_qt_gui_module_exposes_main_window(self):
        from xmum_moodle_downloader import gui_qt

        self.assertTrue(hasattr(gui_qt, "MoodleDownloaderQtWindow"))

    def test_qt_window_has_modern_shell_and_locked_navigation(self):
        qt_app()
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import QGraphicsDropShadowEffect, QStackedLayout

        from xmum_moodle_downloader.gui_qt import AnimatedButton, LightBackdrop, MoodleDownloaderQtWindow

        with tempfile.TemporaryDirectory() as tmp:
            window = MoodleDownloaderQtWindow(Path(tmp))

            self.assertEqual(window.windowTitle(), "XMUM Moodle Downloader")
            self.assertTrue(window.windowFlags() & Qt.FramelessWindowHint)
            self.assertTrue(window.testAttribute(Qt.WA_TranslucentBackground))
            self.assertIsInstance(window.backdrop, LightBackdrop)
            root_stack = window.centralWidget().layout()
            self.assertIsInstance(root_stack, QStackedLayout)
            self.assertEqual(root_stack.currentWidget().objectName(), "shellRoot")
            self.assertIsInstance(window.window_container.graphicsEffect(), QGraphicsDropShadowEffect)
            self.assertEqual(window.title_bar.height(), 46)
            self.assertIsInstance(window.title_bar.minimize_button, AnimatedButton)
            self.assertIsInstance(window.title_bar.close_button, AnimatedButton)
            self.assertFalse(hasattr(window.title_bar, "maximize_button"))
            self.assertEqual(set(window.nav_buttons), {"home", "courses"})
            self.assertTrue(window.nav_buttons["home"].isEnabled())
            self.assertFalse(window.nav_buttons["courses"].isEnabled())
            self.assertEqual(window.status_label.text(), "登录 Moodle 后开始")
            self.assertIn("Microsoft YaHei UI", window.styleSheet())
            self.assertIn("Segoe UI", window.styleSheet())
            self.assertTrue(window.app_icon.exists())

            window.close()

    def test_qt_shell_exposes_independent_view_classes_and_animated_buttons(self):
        qt_app()
        from xmum_moodle_downloader.gui_qt import AnimatedButton, CoursesView, HomeView, MoodleDownloaderQtWindow, Sidebar

        with tempfile.TemporaryDirectory() as tmp:
            window = MoodleDownloaderQtWindow(Path(tmp))
            stylesheet = window.styleSheet()

            self.assertIsInstance(window.sidebar, Sidebar)
            self.assertIsInstance(window.page_widgets["home"], HomeView)
            self.assertIsInstance(window.page_widgets["courses"], CoursesView)
            self.assertIsInstance(window.sidebar_login_button, AnimatedButton)
            self.assertIsInstance(window.splash_login_button, AnimatedButton)
            self.assertIsInstance(window.download_button, AnimatedButton)
            self.assertIsInstance(window.page_widgets["courses"].open_button, AnimatedButton)
            for button in window.nav_buttons.values():
                self.assertIsInstance(button, AnimatedButton)
            self.assertTrue(window.nav_buttons["courses"].icon().isNull())
            self.assertIn("QCheckBox::indicator:checked", stylesheet)
            self.assertIn("QTableWidget::indicator:checked", stylesheet)
            self.assertIn("image: url(data:image/svg+xml;base64,", stylesheet)

            window.close()

    def test_qt_visual_theme_uses_backdrop_as_internal_translucent_background(self):
        qt_app()
        from PySide6.QtWidgets import QStackedLayout

        from xmum_moodle_downloader.gui_qt import LightBackdrop, MoodleDownloaderQtWindow, _mix_color

        transparent_white = _mix_color("rgba(255, 255, 255, 0)", "#eaf3ff", 0)
        self.assertEqual(transparent_white.red(), 255)
        self.assertEqual(transparent_white.green(), 255)
        self.assertEqual(transparent_white.blue(), 255)
        self.assertEqual(transparent_white.alpha(), 0)

        with tempfile.TemporaryDirectory() as tmp:
            window = MoodleDownloaderQtWindow(Path(tmp))
            stylesheet = window.styleSheet()
            container_stack = window.window_container.layout()

            self.assertIsInstance(container_stack, QStackedLayout)
            self.assertIsInstance(window.backdrop, LightBackdrop)
            self.assertIn("Segoe UI", stylesheet)
            self.assertLess(stylesheet.index('"Segoe UI"'), stylesheet.index('"Microsoft YaHei"'))
            self.assertIn("Microsoft YaHei UI", stylesheet)
            self.assertIn("QFrame#windowContainer {\n    background: rgba(255, 255, 255, 42);", stylesheet)
            self.assertIn("QFrame#mainArea {\n    background: transparent;", stylesheet)
            self.assertIn("QPushButton#navButton {\n    text-align: left;", stylesheet)
            self.assertIn("font-size: 12pt;", stylesheet)
            self.assertGreaterEqual(window.sidebar.width(), 248)
            self.assertEqual(window.nav_buttons["home"].height(), 46)
            self.assertEqual(window.nav_buttons["home"].maximumHeight(), 46)
            self.assertLessEqual(window.page_widgets["home"].login_button.height(), 38)

            window.close()

    def test_child_dialogs_use_opaque_light_surfaces_and_visible_standard_buttons(self):
        qt_app()
        from PySide6.QtWidgets import QMessageBox

        from xmum_moodle_downloader.gui_qt import LoginDialog, MoodleDownloaderQtWindow

        with tempfile.TemporaryDirectory() as tmp:
            window = MoodleDownloaderQtWindow(Path(tmp))
            stylesheet = window.styleSheet()

            self.assertIn("QDialog, QMessageBox {", stylesheet)
            self.assertIn("background: #f6faff;", stylesheet)
            self.assertIn("QDialog QPushButton, QMessageBox QPushButton {", stylesheet)
            self.assertIn("background: rgba(255, 255, 255, 210);", stylesheet)
            self.assertIn("QMessageBox QLabel {", stylesheet)

            dialog = LoginDialog(window)
            self.assertEqual(dialog.styleSheet(), window.styleSheet())

            message_box = window._build_message_box(QMessageBox.Information, "登录完成", "Moodle 登录成功。")
            self.assertEqual(message_box.objectName(), "messageBox")
            self.assertEqual(message_box.windowTitle(), "登录完成")
            self.assertEqual(message_box.icon(), QMessageBox.Information)
            self.assertEqual(message_box.styleSheet(), window.styleSheet())

            message_box.close()
            dialog.close()
            window.close()

    def test_login_success_selects_current_term_courses_by_default(self):
        qt_app()
        from xmum_moodle_downloader.gui_qt import MoodleDownloaderQtWindow

        courses = [
            Course("CYS202 Principles of Operating Systems 2026/04 Venantius", "https://example.test/1"),
            Course("CST101 Software Engineering 2025/09 Lecturer", "https://example.test/2"),
            Course("CYS201 Modern Cryptography 2026/04 Iftekhar", "https://example.test/3"),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            window = MoodleDownloaderQtWindow(Path(tmp))
            with patch.object(window, "_show_info"):
                window._handle_login_success(courses)

            self.assertTrue(window.logged_in)
            self.assertEqual(window.selected_term_combo.currentText(), "2026/04")
            self.assertEqual(window.selected_course_urls, {"https://example.test/1", "https://example.test/3"})
            self.assertEqual(window.active_page, "courses")
            self.assertIn("2", window.selected_count_label.text())

            window.close()

    def test_main_opens_qt_app_without_forcing_windows_dpi_awareness(self):
        from xmum_moodle_downloader import gui_qt

        events = []
        app = Mock()
        window = Mock()
        app.exec.side_effect = lambda: events.append("exec") or 0
        window.show.side_effect = lambda: events.append("show")

        with patch.object(gui_qt, "enable_windows_dpi_awareness", side_effect=lambda: events.append("dpi")):
            with patch.object(gui_qt, "_qt_application", side_effect=lambda argv: events.append("app") or app):
                with patch.object(gui_qt, "MoodleDownloaderQtWindow", side_effect=lambda root: events.append("window") or window):
                    result = gui_qt.main([])

        self.assertEqual(result, 0)
        self.assertEqual(events, ["app", "window", "show", "exec"])

    def test_empty_download_selection_shows_warning_without_starting_worker(self):
        qt_app()
        from xmum_moodle_downloader.gui_qt import MoodleDownloaderQtWindow

        with tempfile.TemporaryDirectory() as tmp:
            window = MoodleDownloaderQtWindow(Path(tmp))
            window.logged_in = True
            window.current_courses = [Course("CYS202 2026/04", "https://example.test/1")]
            window.selected_course_urls.clear()
            with patch.object(window, "_show_warning") as warning:
                with patch("threading.Thread") as thread_cls:
                    window._run_download_selected_courses()

            warning.assert_called_once()
            thread_cls.assert_not_called()
            window.close()


if __name__ == "__main__":
    unittest.main()
