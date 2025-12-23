import logging

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
from qasync import asyncSlot

from backend.common.services.newsletter_service import newsletter_service
from backend.desktop.security import get_secret
from backend.desktop.ui.settings_dialog import SettingsDialog

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(self, user_id: int):
        super().__init__()
        self.user_id = user_id
        self.setWindowTitle("AeroBrief AI Newsletter")
        self.resize(900, 700)

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

    def open_settings(self) -> None:
        dlg = SettingsDialog(self)
        dlg.exec()

    @asyncSlot()
    async def start_generation(self) -> None:
        topic = self.topic_input.text().strip()
        context = self.context_input.toPlainText().strip()

        if not topic:
            self.output_area.setText("Please enter a topic.")
            return

        self.generate_btn.setEnabled(False)
        self.output_area.setText(f"Starting research on '{topic}'... This may take a minute.")

        try:
            api_keys = {
                "openai_api_key": get_secret("openai_api_key"),
                "serper_api_key": get_secret("serper_api_key"),
            }
            result = await newsletter_service.generate_newsletter(topic, self.user_id, context, api_keys)
            self.output_area.setMarkdown(result.content)
        except Exception as exc:
            logger.exception("Newsletter generation failed: %s", exc)
            self.output_area.setText("Error occurred while generating the newsletter.")
        finally:
            self.generate_btn.setEnabled(True)
