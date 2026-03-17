import logging
import queue as std_queue
import time

from PySide6.QtCore import QTimer
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QTextEdit,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from backend.desktop.security import get_secret
from backend.desktop.services.ai_worker import AIWorker
from backend.desktop.services.ocr_worker import OCRWorker
from backend.desktop.telemetry_manager import TelemetryManager
from backend.desktop.ui.global_hotkey import GlobalHotkeyManager
from backend.desktop.ui.overlay import ScreenSnipperOverlay
from backend.desktop.ui.settings_dialog import SettingsDialog
from backend.desktop.ui.signal_bus import get_signal_bus

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(
        self,
        user_id: int,
        session_id: str,
        ingestion_queue=None,
        status_queue=None,
        api_process=None,
        api_stop_event=None,
        bridge_warning: str | None = None,
    ) -> None:
        super().__init__()
        self.user_id = user_id
        self.session_id = session_id
        self._ingestion_queue = ingestion_queue
        self._status_queue = status_queue
        self._api_process = api_process
        self._api_stop_event = api_stop_event
        self._bridge_started = False
        self._bridge_disabled = False
        self._bridge_deadline = None
        self._ipc_timer: QTimer | None = None

        self._ai_worker: AIWorker | None = None
        self._ocr_worker: OCRWorker | None = None
        self._context_fragments: list[str] = []

        self.setWindowTitle("AeroBrief AI Newsletter")
        self.resize(900, 700)
        self.setAcceptDrops(True)
        self.statusBar()

        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)

        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.open_settings)
        toolbar.addAction(settings_action)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        layout.addWidget(QLabel("Newsletter Topic:"))
        self.topic_input = QLineEdit()
        self.topic_input.setPlaceholderText("e.g. AI Agents in 2025")
        layout.addWidget(self.topic_input)

        layout.addWidget(QLabel("Context / Instructions:"))
        self.context_input = QTextEdit()
        self.context_input.setPlaceholderText("Enter extra context or focus areas...")
        self.context_input.setMaximumHeight(100)
        layout.addWidget(self.context_input)

        self.generate_btn = QPushButton("Generate Newsletter")
        self.generate_btn.clicked.connect(self.start_generation)
        layout.addWidget(self.generate_btn)

        layout.addWidget(QLabel("Output:"))
        self.output_area = QTextEdit()
        self.output_area.setReadOnly(True)
        layout.addWidget(self.output_area)

        self.signal_bus = get_signal_bus()
        self.signal_bus.status_message.connect(self.show_status)
        self.signal_bus.log_message.connect(self.log_message)
        self.signal_bus.progress_update.connect(self.on_ai_progress)
        self.signal_bus.result_ready.connect(self.on_ai_result)
        self.signal_bus.ingest_received.connect(self.on_ingest_payload)
        self.signal_bus.ocr_requested.connect(self.start_ocr)
        self.signal_bus.ocr_result.connect(self.on_ocr_result)
        self.signal_bus.ocr_error.connect(self.on_ocr_error)
        self.signal_bus.snip_requested.connect(self.activate_snipper)

        self.overlay = ScreenSnipperOverlay(self.signal_bus)
        self.hotkey_manager = GlobalHotkeyManager(self.signal_bus)
        self.hotkey_manager.register()

        self.telemetry = TelemetryManager(user_id=user_id, session_id=session_id, output=self.output_area)
        QTimer.singleShot(0, self.telemetry.start)

        if self._api_process is not None:
            self._bridge_deadline = time.monotonic() + 5.0

        if self._ingestion_queue is not None or self._status_queue is not None or self._api_process is not None:
            self._ipc_timer = QTimer(self)
            self._ipc_timer.setInterval(200)
            self._ipc_timer.timeout.connect(self._poll_ipc)
            self._ipc_timer.start()

        if bridge_warning:
            self.signal_bus.log_message.emit(bridge_warning)
            self.signal_bus.status_message.emit("Browser bridge disabled for this session.")

    def open_settings(self) -> None:
        dlg = SettingsDialog(self)
        dlg.exec()

    def start_generation(self) -> None:
        topic = self.topic_input.text().strip()
        context = self.context_input.toPlainText().strip()

        if not topic:
            self.log_message("Please enter a topic.")
            return

        if self._ai_worker and self._ai_worker.isRunning():
            self.show_status("Generation already running.")
            return

        self.telemetry.flush_output_time()
        self.telemetry.emit_generation(topic, context)

        self.generate_btn.setEnabled(False)
        self.output_area.setText(
            f"Starting research on '{topic}'... This may take a minute."
        )

        api_keys = {
            "openai_api_key": get_secret("openai_api_key"),
            "serper_api_key": get_secret("serper_api_key"),
        }

        self._ai_worker = AIWorker(topic, context, self.user_id, self.session_id, api_keys)
        self._ai_worker.progress_update.connect(self.signal_bus.progress_update)
        self._ai_worker.status_message.connect(self.signal_bus.status_message)
        self._ai_worker.result_ready.connect(self.signal_bus.result_ready)
        self._ai_worker.finished.connect(self.on_ai_finished)
        self._ai_worker.start()

    def start_ocr(self, image) -> None:
        if self._ocr_worker and self._ocr_worker.isRunning():
            self.show_status("OCR already running.")
            return
        self._ocr_worker = OCRWorker(image)
        self._ocr_worker.status_message.connect(self.signal_bus.status_message)
        self._ocr_worker.result_ready.connect(self.signal_bus.ocr_result)
        self._ocr_worker.error_message.connect(self.signal_bus.ocr_error)
        self._ocr_worker.start()

    def show_status(self, message: str) -> None:
        self.statusBar().showMessage(message, 5000)

    def log_message(self, message: str) -> None:
        self.output_area.append(message)

    def on_ai_progress(self, progress: int) -> None:
        self.statusBar().showMessage(f"Progress: {progress}%", 3000)

    def on_ai_result(self, result: str) -> None:
        if result:
            self.output_area.setMarkdown(result)
            self.telemetry.mark_output_start()
        else:
            self.output_area.setText("No output generated.")

    def on_ai_finished(self) -> None:
        self.generate_btn.setEnabled(True)

    def on_ocr_result(self, text: str) -> None:
        if text:
            self.output_area.append("OCR Result:\n" + text)
            self._append_context("Screen OCR", text)
        else:
            self.output_area.append("OCR completed with no text detected.")

    def on_ocr_error(self, message: str) -> None:
        self.output_area.append(message)

    def on_ingest_payload(self, payload: dict) -> None:
        url = payload.get("url") or ""
        text = payload.get("text") or ""
        if url:
            self.output_area.append(f"Ingestion received: {url}")
            self._append_context("Bridge URL", url)
        if text:
            preview = text[:200] + ("..." if len(text) > 200 else "")
            self.output_area.append(f"Ingested text preview: {preview}")
            self._append_context("Bridge Text", text)

    def activate_snipper(self) -> None:
        self.overlay.activate()

    def _poll_ipc(self) -> None:
        self._drain_ingestion_queue()
        self._drain_status_queue()
        self._check_bridge_health()

    def _drain_ingestion_queue(self) -> None:
        if self._ingestion_queue is None:
            return
        while True:
            try:
                payload = self._ingestion_queue.get_nowait()
            except std_queue.Empty:
                break
            self.signal_bus.ingest_received.emit(payload)

    def _drain_status_queue(self) -> None:
        if self._status_queue is None:
            return
        while True:
            try:
                message = self._status_queue.get_nowait()
            except std_queue.Empty:
                break
            status = message.get("status")
            port = message.get("port")
            if status == "starting":
                if port:
                    self.show_status(f"Bridge starting on port {port}...")
                else:
                    self.show_status("Bridge starting...")
            elif status == "started":
                self._bridge_started = True
                if port:
                    self.signal_bus.log_message.emit(f"Browser bridge started on port {port}.")
                    self.show_status(f"Bridge ready on port {port}.")
                else:
                    self.signal_bus.log_message.emit("Browser bridge started.")
                    self.show_status("Bridge ready.")
            elif status == "failed":
                error = message.get("error") or "Bridge failed."
                self._disable_bridge(error)

    def _check_bridge_health(self) -> None:
        if self._bridge_disabled:
            return
        if self._api_process is not None and not self._api_process.is_alive():
            if not self._bridge_started:
                self._disable_bridge("Bridge failed to start.")
            else:
                self._disable_bridge("Bridge stopped unexpectedly.")
            return

        if self._bridge_deadline and not self._bridge_started:
            if time.monotonic() > self._bridge_deadline:
                self._disable_bridge("Bridge unreachable.")

    def _disable_bridge(self, reason: str) -> None:
        if self._bridge_disabled:
            return
        self._bridge_disabled = True
        self.signal_bus.log_message.emit(f"Browser bridge disabled: {reason}")
        self.signal_bus.status_message.emit("Browser bridge disabled.")
        if self._api_stop_event is not None:
            self._api_stop_event.set()

    def _append_context(self, label: str, content: str) -> None:
        content = content.strip()
        if not content:
            return
        block = f"[{label}]\n{content}"
        if block in self._context_fragments:
            return
        self._context_fragments.append(block)
        current = self.context_input.toPlainText().strip()
        combined = "\n\n".join([current] + self._context_fragments if current else self._context_fragments)
        self.context_input.setPlainText(combined)

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event) -> None:
        if not event.mimeData().hasUrls():
            return
        paths = [url.toLocalFile() for url in event.mimeData().urls()]
        self.telemetry.handle_file_drop(paths)

    def closeEvent(self, event) -> None:
        self.telemetry.flush_output_time()
        self.telemetry.emit_session_end()
        self.telemetry.shutdown()

        self.hotkey_manager.unregister()
        if self._ipc_timer is not None:
            self._ipc_timer.stop()

        if self._ocr_worker and self._ocr_worker.isRunning():
            self._ocr_worker.cancel()
            self._ocr_worker.wait(2000)
        if self._ai_worker and self._ai_worker.isRunning():
            self._ai_worker.cancel()
            self._ai_worker.wait(2000)

        if self._api_stop_event is not None:
            self._api_stop_event.set()
        if self._api_process is not None:
            self._api_process.join(timeout=3)
            if self._api_process.is_alive():
                self._api_process.terminate()
                self._api_process.join(timeout=1)

        super().closeEvent(event)
