import ctypes
import os
from pathlib import Path


APPLE_THEME = {
    "app_bg": "#f5f5f7",
    "sidebar_bg": "#f2f2f7",
    "surface": "#ffffff",
    "surface_alt": "#fbfbfd",
    "border": "#d2d2d7",
    "border_soft": "#e5e5ea",
    "text": "#1d1d1f",
    "text_secondary": "#86868b",
    "text_tertiary": "#86868b",
    "primary": "#0071e3",
    "primary_active": "#0066cc",
    "primary_disabled": "#a8cff5",
    "nav_active": "#e8e8ed",
}


def asset_path(name: str) -> Path:
    return Path(__file__).with_name("assets") / name


def app_icon_path() -> Path:
    return asset_path("xmum.ico")


def course_icon_path() -> Path:
    return asset_path("course.png")


def ensure_icon_assets() -> None:
    missing = [path for path in (app_icon_path(), course_icon_path()) if not path.exists()]
    if missing:
        names = ", ".join(str(path) for path in missing)
        raise FileNotFoundError(f"Missing GUI asset(s): {names}")


def enable_windows_dpi_awareness() -> None:
    if os.name != "nt":
        return None
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            return None
    return None
