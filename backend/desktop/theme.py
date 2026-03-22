from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from qt_material import apply_stylesheet

from backend.desktop.preferences import get_theme_mode

THEME_MODE_SYSTEM = "system"
THEME_MODE_DARK = "dark"
THEME_MODE_LIGHT = "light"

_THEME_FILES = {
    THEME_MODE_DARK: "dark_teal.xml",
    THEME_MODE_LIGHT: "light_cyan.xml",
}


def normalize_theme_mode(mode: str | None) -> str:
    if not mode:
        return THEME_MODE_SYSTEM
    lowered = mode.strip().lower()
    if lowered in {THEME_MODE_SYSTEM, THEME_MODE_DARK, THEME_MODE_LIGHT}:
        return lowered
    return THEME_MODE_SYSTEM


def detect_system_theme_mode(app: QApplication | None = None) -> str:
    qt_app = app or QApplication.instance()
    if qt_app is None:
        return THEME_MODE_DARK
    try:
        scheme = qt_app.styleHints().colorScheme()
    except Exception:
        return THEME_MODE_DARK
    return THEME_MODE_DARK if scheme == Qt.ColorScheme.Dark else THEME_MODE_LIGHT


def resolve_effective_theme_mode(mode: str | None, app: QApplication | None = None) -> str:
    normalized = normalize_theme_mode(mode)
    if normalized == THEME_MODE_SYSTEM:
        return detect_system_theme_mode(app)
    return normalized


def apply_app_theme(app: QApplication, mode: str | None = None) -> str:
    preference = normalize_theme_mode(mode or get_theme_mode())
    effective = resolve_effective_theme_mode(preference, app)
    apply_stylesheet(app, theme=_THEME_FILES[effective])
    app.setProperty("lumeward.theme_preference", preference)
    app.setProperty("lumeward.theme_effective", effective)
    return effective


def install_system_theme_listener(app: QApplication) -> None:
    style_hints = app.styleHints()
    signal = getattr(style_hints, "colorSchemeChanged", None)
    if signal is None:
        return

    def _refresh_theme(*_args) -> None:
        if normalize_theme_mode(get_theme_mode()) == THEME_MODE_SYSTEM:
            apply_app_theme(app, THEME_MODE_SYSTEM)

    signal.connect(_refresh_theme)
