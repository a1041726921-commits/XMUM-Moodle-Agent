import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from .config import _read_env_file


DEFAULT_MODEL_PROVIDERS = [
    {
        "id": "openai",
        "name": "OpenAI",
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4o-mini",
        "api_key": "",
        "enabled": False,
    },
    {
        "id": "deepseek",
        "name": "DeepSeek",
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-chat",
        "api_key": "",
        "enabled": False,
    },
    {
        "id": "qwen",
        "name": "Alibaba Qwen",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model": "qwen-plus",
        "api_key": "",
        "enabled": False,
    },
    {
        "id": "gemini",
        "name": "Google Gemini",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "model": "gemini-1.5-flash",
        "api_key": "",
        "enabled": False,
    },
    {
        "id": "anthropic",
        "name": "Anthropic Claude",
        "base_url": "https://api.anthropic.com/v1",
        "model": "claude-3-5-haiku-latest",
        "api_key": "",
        "enabled": False,
    },
]


@dataclass
class GuiSettings:
    moodle_username: str = ""
    moodle_password: str = ""
    remember_password: bool = False
    auto_login: bool = False
    model_providers: List[Dict[str, object]] = field(default_factory=list)


def load_gui_settings(root: Path) -> GuiSettings:
    root = root.resolve()
    env_values = _read_env_file(root / ".env")
    state = _read_json(root / "state" / "gui-settings.json")

    providers = _merge_model_providers(state.get("model_providers", []))
    remember_password = bool(state.get("remember_password", bool(env_values.get("XMUM_MOODLE_PASSWORD"))))

    return GuiSettings(
        moodle_username=str(env_values.get("XMUM_MOODLE_USERNAME", "")),
        moodle_password=str(env_values.get("XMUM_MOODLE_PASSWORD", "")) if remember_password else "",
        remember_password=remember_password,
        auto_login=bool(state.get("auto_login", False)),
        model_providers=providers,
    )


def save_gui_settings(root: Path, settings: GuiSettings) -> None:
    root = root.resolve()
    (root / "state").mkdir(parents=True, exist_ok=True)
    _write_env_file(root / ".env", settings)

    state = {
        "remember_password": settings.remember_password,
        "auto_login": settings.auto_login,
        "model_providers": _merge_model_providers(settings.model_providers),
    }
    (root / "state" / "gui-settings.json").write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def can_generate_notes(settings: GuiSettings) -> bool:
    return any(
        bool(provider.get("enabled")) and bool(str(provider.get("api_key", "")).strip())
        for provider in settings.model_providers
    )


def _read_json(path: Path) -> Dict[str, object]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _merge_model_providers(saved_providers) -> List[Dict[str, object]]:
    saved_by_id = {
        str(provider.get("id")): provider
        for provider in saved_providers
        if isinstance(provider, dict) and provider.get("id")
    }
    providers: List[Dict[str, object]] = []
    for default_provider in DEFAULT_MODEL_PROVIDERS:
        saved = saved_by_id.get(default_provider["id"], {})
        merged = dict(default_provider)
        merged.update(
            {
                "base_url": str(saved.get("base_url", default_provider["base_url"])),
                "model": str(saved.get("model", default_provider["model"])),
                "api_key": str(saved.get("api_key", "")),
                "enabled": bool(saved.get("enabled", False)),
            }
        )
        providers.append(merged)
    return providers


def _write_env_file(path: Path, settings: GuiSettings) -> None:
    existing = _read_env_file(path)
    existing["XMUM_MOODLE_USERNAME"] = settings.moodle_username.strip()
    existing["XMUM_MOODLE_PASSWORD"] = settings.moodle_password if settings.remember_password else ""
    existing.setdefault("XMUM_MOODLE_COURSES_URL", "https://l.xmu.edu.my/my/")
    existing.setdefault("XMUM_AGENT_DATA_DIR", "data")
    existing.setdefault("XMUM_AGENT_HEADLESS", "true")
    existing.setdefault("XMUM_COURSE_INCLUDE_REGEX", "2026/04")
    existing.setdefault("XMUM_COURSE_EXCLUDE_REGEX", "")

    ordered_keys = [
        "XMUM_MOODLE_USERNAME",
        "XMUM_MOODLE_PASSWORD",
        "XMUM_MOODLE_COURSES_URL",
        "XMUM_AGENT_DATA_DIR",
        "XMUM_AGENT_HEADLESS",
        "XMUM_COURSE_INCLUDE_REGEX",
        "XMUM_COURSE_EXCLUDE_REGEX",
    ]
    lines = [f"{key}={existing.get(key, '')}" for key in ordered_keys]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
