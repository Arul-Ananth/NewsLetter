from __future__ import annotations

from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtGui import QColor, QGuiApplication, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QWidget

from backend.desktop.ui.signal_bus import SignalBus


class ScreenSnipperOverlay(QWidget):
    def __init__(self, signal_bus: SignalBus) -> None:
        super().__init__(None, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self._signal_bus = signal_bus
        self._origin: QPoint | None = None
        self._current: QPoint | None = None
        self._capture: QPixmap | None = None

        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(True)

    def activate(self) -> None:
        self._origin = None
        self._current = None
        self._set_geometry()
        self._capture_screen()
        self.show()
        self.raise_()
        self.activateWindow()

    def _set_geometry(self) -> None:
        virtual = QGuiApplication.primaryScreen().virtualGeometry()
        self.setGeometry(virtual)

    def _capture_screen(self) -> None:
        virtual = QGuiApplication.primaryScreen().virtualGeometry()
        composed = QPixmap(virtual.size())
        composed.fill(Qt.transparent)
        painter = QPainter(composed)
        for screen in QGuiApplication.screens():
            grab = screen.grabWindow(0)
            top_left = screen.geometry().topLeft() - virtual.topLeft()
            painter.drawPixmap(top_left, grab)
        painter.end()
        self._capture = composed

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        if self._capture:
            painter.drawPixmap(0, 0, self._capture)
        painter.setPen(QPen(QColor(255, 0, 0), 2))
        if self._origin and self._current:
            rect = QRect(self._origin, self._current).normalized()
            painter.drawRect(rect)

    def mousePressEvent(self, event) -> None:
        self._origin = event.position().toPoint()
        self._current = self._origin
        self.update()

    def mouseMoveEvent(self, event) -> None:
        if not self._origin:
            return
        self._current = event.position().toPoint()
        self.update()

    def mouseReleaseEvent(self, event) -> None:
        if not self._origin:
            self.hide()
            return
        self._current = event.position().toPoint()
        rect = QRect(self._origin, self._current).normalized()
        self.hide()
        if rect.width() < 5 or rect.height() < 5:
            return
        if not self._capture:
            return
        dpr = self._capture.devicePixelRatio()
        scaled = QRect(
            int(rect.x() * dpr),
            int(rect.y() * dpr),
            int(rect.width() * dpr),
            int(rect.height() * dpr),
        )
        cropped = self._capture.copy(scaled)
        cropped.setDevicePixelRatio(dpr)
        self._signal_bus.ocr_requested.emit(cropped.toImage())
