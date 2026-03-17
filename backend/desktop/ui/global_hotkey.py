from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes

from PySide6.QtCore import QAbstractNativeEventFilter, QCoreApplication

WM_HOTKEY = 0x0312
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
VK_S = 0x53


class _HotkeyFilter(QAbstractNativeEventFilter):
    def __init__(self, callback, hotkey_id: int) -> None:
        super().__init__()
        self._callback = callback
        self._hotkey_id = hotkey_id

    def nativeEventFilter(self, eventType, message):
        if eventType not in ("windows_generic_MSG", "windows_dispatcher_MSG"):
            return False, 0
        msg = wintypes.MSG.from_address(int(message))
        if msg.message == WM_HOTKEY and msg.wParam == self._hotkey_id:
            self._callback()
            return True, 0
        return False, 0


class GlobalHotkeyManager:
    def __init__(self, signal_bus) -> None:
        self._signal_bus = signal_bus
        self._hotkey_id = 1
        self._filter = None
        self._registered = False
        self._user32 = None

    def register(self) -> bool:
        if sys.platform != "win32":
            self._signal_bus.status_message.emit("Global hotkey not supported on this OS.")
            return False
        self._user32 = ctypes.windll.user32
        self._filter = _HotkeyFilter(self._emit_hotkey, self._hotkey_id)
        QCoreApplication.instance().installNativeEventFilter(self._filter)
        if not self._user32.RegisterHotKey(None, self._hotkey_id, MOD_CONTROL | MOD_ALT, VK_S):
            err = ctypes.get_last_error()
            self._signal_bus.status_message.emit(
                f"Global hotkey registration failed (error {err})."
            )
            return False
        self._registered = True
        self._signal_bus.status_message.emit("Global hotkey registered: Ctrl+Alt+S")
        return True

    def unregister(self) -> None:
        if sys.platform != "win32":
            return
        if self._registered and self._user32:
            try:
                self._user32.UnregisterHotKey(None, self._hotkey_id)
            except Exception:
                pass
        self._registered = False

    def _emit_hotkey(self) -> None:
        self._signal_bus.snip_requested.emit()
