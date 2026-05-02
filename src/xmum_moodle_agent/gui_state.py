import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

from .config import AgentConfig, _as_bool, _get_optional_value, _get_value, _read_env_file


@dataclass
class GuiSettings:
    moodle_username: str = ""
    moodle_password: str = ""
    remember_password: bool = False
    auto_login: bool = False


def load_gui_settings(root: Path) -> GuiSettings:
    root = root.resolve()
    env_values = _read_env_file(root / ".env")
    state = _read_json(root / "state" / "gui-settings.json")

    remember_password = bool(state.get("remember_password", bool(env_values.get("XMUM_MOODLE_PASSWORD"))))

    return GuiSettings(
        moodle_username=str(env_values.get("XMUM_MOODLE_USERNAME", "")),
        moodle_password=str(env_values.get("XMUM_MOODLE_PASSWORD", "")) if remember_password else "",
        remember_password=remember_password,
        auto_login=bool(state.get("auto_login", False)),
    )


def save_gui_settings(root: Path, settings: GuiSettings) -> None:
    root = root.resolve()
    (root / "state").mkdir(parents=True, exist_ok=True)
    _write_env_file(root / ".env", settings)

    state = {
        "remember_password": settings.remember_password,
        "auto_login": settings.auto_login,
    }
    (root / "state" / "gui-settings.json").write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def agent_config_from_gui_settings(root: Path, settings: GuiSettings) -> AgentConfig:
    root = root.resolve()
    env_values = _read_env_file(root / ".env")
    data_dir_value = _get_value("XMUM_AGENT_DATA_DIR", env_values) or "data"
    data_dir = Path(data_dir_value)
    if not data_dir.is_absolute():
        data_dir = root / data_dir

    moodle_courses_url = _get_value("XMUM_MOODLE_COURSES_URL", env_values) or "https://l.xmu.edu.my/my/"

    return AgentConfig(
        root=root,
        username=settings.moodle_username.strip(),
        password=settings.moodle_password,
        moodle_courses_url=moodle_courses_url,
        data_dir=data_dir,
        courses_dir=data_dir / "courses",
        index_path=data_dir / "index.json",
        headless=_as_bool(_get_value("XMUM_AGENT_HEADLESS", env_values), default=True),
        course_include_regex=_get_optional_value("XMUM_COURSE_INCLUDE_REGEX", env_values),
        course_exclude_regex=_get_optional_value("XMUM_COURSE_EXCLUDE_REGEX", env_values),
    )


def _read_json(path: Path) -> Dict[str, object]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _write_env_file(path: Path, settings: GuiSettings) -> None:
    existing = _read_env_file(path)
    existing["XMUM_MOODLE_USERNAME"] = settings.moodle_username.strip()
    existing["XMUM_MOODLE_PASSWORD"] = settings.moodle_password if settings.remember_password else ""
    existing.setdefault("XMUM_MOODLE_COURSES_URL", "https://l.xmu.edu.my/my/")
    existing.setdefault("XMUM_AGENT_DATA_DIR", "data")
    existing.setdefault("XMUM_AGENT_HEADLESS", "true")
    existing.setdefault("XMUM_COURSE_INCLUDE_REGEX", "")
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
