import json
import tempfile
import unittest
from pathlib import Path

from xmum_moodle_agent.gui_state import (
    DEFAULT_MODEL_PROVIDERS,
    GuiSettings,
    agent_config_from_gui_settings,
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
            ["openai", "google", "anthropic", "alibaba", "xiaomi", "deepseek"],
        )
        self.assertFalse(can_generate_notes(settings))

    def test_legacy_provider_ids_are_migrated_to_new_company_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "state").mkdir()
            (root / "state" / "gui-settings.json").write_text(
                json.dumps(
                    {
                        "model_providers": [
                            {
                                "id": "gemini",
                                "base_url": "https://old-google.test",
                                "api_key": "google-key",
                                "enabled": True,
                            },
                            {
                                "id": "qwen",
                                "base_url": "https://old-alibaba.test",
                                "api_key": "alibaba-key",
                                "enabled": True,
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )

            settings = load_gui_settings(root)

        providers = {provider["id"]: provider for provider in settings.model_providers}
        self.assertEqual(providers["google"]["api_key"], "google-key")
        self.assertEqual(providers["google"]["base_url"], "https://old-google.test")
        self.assertEqual(providers["google"]["model"], "gemini-3-flash-preview")
        self.assertEqual(providers["alibaba"]["api_key"], "alibaba-key")
        self.assertEqual(providers["alibaba"]["base_url"], "https://old-alibaba.test")

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

    def test_saved_model_override_is_ignored_because_models_are_internal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "state").mkdir()
            (root / "state" / "gui-settings.json").write_text(
                json.dumps(
                    {
                        "model_providers": [
                            {
                                "id": "openai",
                                "name": "OpenAI",
                                "base_url": "https://api.openai.com/v1",
                                "model": "user-picked-model",
                                "api_key": "sk-test",
                                "enabled": True,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            settings = load_gui_settings(root)

        openai = next(provider for provider in settings.model_providers if provider["id"] == "openai")
        default_openai = next(provider for provider in DEFAULT_MODEL_PROVIDERS if provider["id"] == "openai")
        self.assertEqual(openai["model"], default_openai["model"])
        self.assertNotEqual(openai["model"], "user-picked-model")

    def test_agent_config_can_use_current_gui_password_without_persisting_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            settings = GuiSettings(
                moodle_username="s1234567",
                moodle_password="window-only-pass",
                remember_password=False,
                auto_login=False,
                model_providers=[],
            )

            config = agent_config_from_gui_settings(root, settings)

        self.assertEqual(config.username, "s1234567")
        self.assertEqual(config.password, "window-only-pass")
        self.assertEqual(config.courses_dir, root / "data" / "courses")
        self.assertIsNone(config.course_include_regex)


if __name__ == "__main__":
    unittest.main()
