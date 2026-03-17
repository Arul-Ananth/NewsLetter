from pathlib import Path

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from backend.common.services.telemetry.consent import add_folder_consent
from backend.desktop.preferences import (
    get_clipboard_collection_enabled,
    get_data_collection_enabled,
    set_clipboard_collection_enabled,
    set_data_collection_enabled,
)
from backend.desktop.security import get_secret, set_secret


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.resize(400, 240)

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("OpenAI API Key (Optional):"))
        self.openai_input = QLineEdit()
        self.openai_input.setEchoMode(QLineEdit.Password)
        self.openai_input.setText(get_secret("openai_api_key") or "")
        layout.addWidget(self.openai_input)

        layout.addWidget(QLabel("Serper API Key (For Web Search):"))
        self.serper_input = QLineEdit()
        self.serper_input.setEchoMode(QLineEdit.Password)
        self.serper_input.setText(get_secret("serper_api_key") or "")
        layout.addWidget(self.serper_input)

        layout.addWidget(QLabel("Watched Folders (opt-in for ingestion):"))
        self.add_folder_btn = QPushButton("Add Folder to Watch")
        self.add_folder_btn.clicked.connect(self.add_folder)
        layout.addWidget(self.add_folder_btn)

        self.data_collection_checkbox = QCheckBox("Enable desktop telemetry data collection")
        self.data_collection_checkbox.setChecked(get_data_collection_enabled())
        self.data_collection_checkbox.toggled.connect(self._on_data_collection_toggled)
        layout.addWidget(self.data_collection_checkbox)

        self.clipboard_collection_checkbox = QCheckBox("Enable clipboard collection (opt-in)")
        self.clipboard_collection_checkbox.setChecked(get_clipboard_collection_enabled())
        layout.addWidget(self.clipboard_collection_checkbox)
        self._on_data_collection_toggled(self.data_collection_checkbox.isChecked())

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.save_settings)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def save_settings(self) -> None:
        openai_key = self.openai_input.text().strip()
        serper_key = self.serper_input.text().strip()

        if openai_key:
            set_secret("openai_api_key", openai_key)
        if serper_key:
            set_secret("serper_api_key", serper_key)

        set_data_collection_enabled(self.data_collection_checkbox.isChecked())
        set_clipboard_collection_enabled(self.clipboard_collection_checkbox.isChecked())

        QMessageBox.information(self, "Settings", "Settings saved.")
        self.accept()

    def add_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select Folder to Watch")
        if not folder:
            return
        add_folder_consent(Path(folder))
        QMessageBox.information(self, "Settings", "Folder consent saved.")

    def _on_data_collection_toggled(self, enabled: bool) -> None:
        self.clipboard_collection_checkbox.setEnabled(enabled)
        if not enabled:
            self.clipboard_collection_checkbox.setChecked(False)
