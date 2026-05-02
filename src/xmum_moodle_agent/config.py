import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional


class ConfigError(RuntimeError):
    """Raised when required agent configuration is missing or invalid."""


@dataclass(frozen=True)
class AgentConfig:
    root: Path
    username: str
    password: str
    moodle_courses_url: str
    data_dir: Path
    courses_dir: Path
    index_path: Path
    headless: bool
    course_include_regex: Optional[str]
    course_exclude_regex: Optional[str]


def _read_env_file(env_file: Path) -> Dict[str, str]:
    values: Dict[str, str] = {}
    if not env_file.exists():
        return values

    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip().lstrip("\ufeff")] = value.strip().strip('"').strip("'")
    return values


def _get_value(key: str, env_values: Dict[str, str]) -> Optional[str]:
    return os.environ.get(key) or env_values.get(key)


def _get_optional_value(key: str, env_values: Dict[str, str], default: Optional[str] = None) -> Optional[str]:
    if key in os.environ:
        value = os.environ[key]
    elif key in env_values:
        value = env_values[key]
    else:
        value = default
    if value is None:
        return None
    value = value.strip()
    return value or None


def _as_bool(value: Optional[str], default: bool = True) -> bool:
    if value is None:
        return default
    return value.strip().lower() not in {"0", "false", "no", "off"}


def load_config(root: Optional[Path] = None, env_file: Optional[Path] = None) -> AgentConfig:
    root = (root or Path.cwd()).resolve()
    env_file = env_file or (root / ".env")
    env_values = _read_env_file(env_file)

    username = _get_value("XMUM_MOODLE_USERNAME", env_values)
    password = _get_value("XMUM_MOODLE_PASSWORD", env_values)
    missing = [
        name
        for name, value in (
            ("XMUM_MOODLE_USERNAME", username),
            ("XMUM_MOODLE_PASSWORD", password),
        )
        if not value
    ]
    if missing:
        raise ConfigError(
            "Missing required Moodle credential(s): "
            + ", ".join(missing)
            + ". Set them in .env or Windows environment variables."
        )

    data_dir_value = _get_value("XMUM_AGENT_DATA_DIR", env_values) or "data"
    data_dir = Path(data_dir_value)
    if not data_dir.is_absolute():
        data_dir = root / data_dir

    moodle_courses_url = (
        _get_value("XMUM_MOODLE_COURSES_URL", env_values)
        or "https://l.xmu.edu.my/my/"
    )

    return AgentConfig(
        root=root,
        username=username or "",
        password=password or "",
        moodle_courses_url=moodle_courses_url,
        data_dir=data_dir,
        courses_dir=data_dir / "courses",
        index_path=data_dir / "index.json",
        headless=_as_bool(_get_value("XMUM_AGENT_HEADLESS", env_values), default=True),
        course_include_regex=_get_optional_value(
            "XMUM_COURSE_INCLUDE_REGEX",
            env_values,
            default=None,
        ),
        course_exclude_regex=_get_optional_value("XMUM_COURSE_EXCLUDE_REGEX", env_values),
    )
