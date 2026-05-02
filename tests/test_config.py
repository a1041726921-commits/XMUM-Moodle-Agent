import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from xmum_moodle_agent.config import ConfigError, load_config


class ConfigTests(unittest.TestCase):
    def test_loads_credentials_from_env_file_and_sets_default_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env_file = root / ".env"
            env_file.write_text(
                "XMUM_MOODLE_USERNAME=student01\n"
                "XMUM_MOODLE_PASSWORD=secret\n",
                encoding="utf-8",
            )

            with patch.dict(os.environ, {}, clear=True):
                config = load_config(root=root, env_file=env_file)

        self.assertEqual(config.username, "student01")
        self.assertEqual(config.password, "secret")
        self.assertEqual(config.moodle_courses_url, "https://l.xmu.edu.my/my/")
        self.assertEqual(config.data_dir, root / "data")
        self.assertEqual(config.courses_dir, root / "data" / "courses")
        self.assertEqual(config.index_path, root / "data" / "index.json")
        self.assertIsNone(config.course_include_regex)
        self.assertIsNone(config.course_exclude_regex)

    def test_environment_overrides_env_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env_file = root / ".env"
            env_file.write_text(
                "XMUM_MOODLE_USERNAME=file-user\n"
                "XMUM_MOODLE_PASSWORD=file-pass\n",
                encoding="utf-8",
            )

            with patch.dict(
                os.environ,
                {
                    "XMUM_MOODLE_USERNAME": "env-user",
                    "XMUM_MOODLE_PASSWORD": "env-pass",
                },
                clear=True,
            ):
                config = load_config(root=root, env_file=env_file)

        self.assertEqual(config.username, "env-user")
        self.assertEqual(config.password, "env-pass")

    def test_course_filter_can_be_overridden_or_disabled(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env_file = root / ".env"
            env_file.write_text(
                "XMUM_MOODLE_USERNAME=student01\n"
                "XMUM_MOODLE_PASSWORD=secret\n"
                "XMUM_COURSE_INCLUDE_REGEX=\n"
                "XMUM_COURSE_EXCLUDE_REGEX=^G\n",
                encoding="utf-8",
            )

            with patch.dict(os.environ, {}, clear=True):
                config = load_config(root=root, env_file=env_file)

        self.assertIsNone(config.course_include_regex)
        self.assertEqual(config.course_exclude_regex, "^G")

    def test_env_file_accepts_utf8_bom(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env_file = root / ".env"
            env_file.write_text(
                "\ufeffXMUM_MOODLE_USERNAME=student01\n"
                "XMUM_MOODLE_PASSWORD=secret\n",
                encoding="utf-8",
            )

            with patch.dict(os.environ, {}, clear=True):
                config = load_config(root=root, env_file=env_file)

        self.assertEqual(config.username, "student01")

    def test_missing_credentials_raise_clear_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {}, clear=True):
                with self.assertRaisesRegex(ConfigError, "XMUM_MOODLE_USERNAME"):
                    load_config(root=Path(tmp), env_file=Path(tmp) / ".env")


if __name__ == "__main__":
    unittest.main()
