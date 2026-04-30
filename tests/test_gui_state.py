import json
import tempfile
import unittest
from pathlib import Path

from xmum_moodle_agent.gui_state import (
    DEFAULT_MODEL_PROVIDERS,
    GuiSettings,
    can_generate_notes,
    load_gui_settings,
    save_gui_settings,
)


class GuiStateTests(unittest.TestCase):
    def test_loads_defaults_when_gui_state_files_do_not_exist(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            settings = load_gui_settings(root)

        self.assertEqual(settings.moodle_username, "")
        self.assertEqual(settings.moodle_password, "")
        self.assertFalse(settings.remember_password)
        self.assertFalse(settings.auto_login)
        self.assertEqual(
            [provider["id"] for provider in settings.model_providers],
            [provider["id"] for provider in DEFAULT_MODEL_PROVIDERS],
        )
        self.assertFalse(can_generate_notes(settings))

    def test_save_without_remember_password_keeps_password_out_of_env_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            settings = GuiSettings(
                moodle_username="s1234567",
                moodle_password="secret-pass",
                remember_password=False,
                auto_login=True,
                model_providers=[],
            )

            save_gui_settings(root, settings)
            env_text = (root / ".env").read_text(encoding="utf-8")
            gui_state = json.loads((root / "state" / "gui-settings.json").read_text(encoding="utf-8"))

        self.assertIn("XMUM_MOODLE_USERNAME=s1234567", env_text)
        self.assertIn("XMUM_MOODLE_PASSWORD=", env_text)
        self.assertNotIn("secret-pass", env_text)
        self.assertFalse(gui_state["remember_password"])
        self.assertTrue(gui_state["auto_login"])

    def test_save_with_remember_password_persists_password_for_existing_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            settings = GuiSettings(
                moodle_username="s1234567",
                moodle_password="secret-pass",
                remember_password=True,
                auto_login=False,
                model_providers=[],
            )

            save_gui_settings(root, settings)
            env_text = (root / ".env").read_text(encoding="utf-8")

        self.assertIn("XMUM_MOODLE_USERNAME=s1234567", env_text)
        self.assertIn("XMUM_MOODLE_PASSWORD=secret-pass", env_text)

    def test_model_api_key_enables_note_generation_choice(self):
        settings = GuiSettings(
            moodle_username="",
            moodle_password="",
            remember_password=False,
            auto_login=False,
            model_providers=[
                {
                    "id": "openai",
                    "name": "OpenAI",
                    "base_url": "https://api.openai.com/v1",
                    "model": "gpt-4o-mini",
                    "api_key": "sk-test",
                    "enabled": True,
                },
                {
                    "id": "deepseek",
                    "name": "DeepSeek",
                    "base_url": "https://api.deepseek.com/v1",
                    "model": "deepseek-chat",
                    "api_key": "",
                    "enabled": True,
                },
            ],
        )

        self.assertTrue(can_generate_notes(settings))


if __name__ == "__main__":
    unittest.main()
