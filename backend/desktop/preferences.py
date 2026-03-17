from __future__ import annotations

from PySide6.QtCore import QSettings

from backend.common.config import settings

_ORG_NAME = "AeroBrief"
_APP_NAME = "AeroBrief"

_KEY_DATA_COLLECTION_ENABLED = "telemetry/data_collection_enabled"
_KEY_CLIPBOARD_COLLECTION_ENABLED = "telemetry/clipboard_collection_enabled"


def _store() -> QSettings:
    return QSettings(_ORG_NAME, _APP_NAME)


def _to_bool(value, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def get_data_collection_enabled() -> bool:
    raw = _store().value(_KEY_DATA_COLLECTION_ENABLED, None)
    return _to_bool(raw, settings.DATA_COLLECTION_ENABLED)


def set_data_collection_enabled(enabled: bool) -> None:
    _store().setValue(_KEY_DATA_COLLECTION_ENABLED, bool(enabled))


def get_clipboard_collection_enabled() -> bool:
    raw = _store().value(_KEY_CLIPBOARD_COLLECTION_ENABLED, None)
    return _to_bool(raw, settings.CLIPBOARD_COLLECTION_ENABLED)


def set_clipboard_collection_enabled(enabled: bool) -> None:
    _store().setValue(_KEY_CLIPBOARD_COLLECTION_ENABLED, bool(enabled))
