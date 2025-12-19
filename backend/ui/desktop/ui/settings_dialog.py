from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QDialogButtonBox, QMessageBox
)
from backend.server.security import set_secret, get_secret

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.resize(400, 200)
        
        layout = QVBoxLayout(self)
        
        # OpenAI Key
        layout.addWidget(QLabel("OpenAI API Key (Optional):"))
        self.openai_input = QLineEdit()
        self.openai_input.setEchoMode(QLineEdit.Password)
        self.openai_input.setText(get_secret("openai_api_key") or "")
        layout.addWidget(self.openai_input)
        
        # Serper Key
        layout.addWidget(QLabel("Serper API Key (For Web Search):"))
        self.serper_input = QLineEdit()
        self.serper_input.setEchoMode(QLineEdit.Password)
        self.serper_input.setText(get_secret("serper_api_key") or "")
        layout.addWidget(self.serper_input)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.save_settings)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
    def save_settings(self):
        openai_key = self.openai_input.text().strip()
        serper_key = self.serper_input.text().strip()
        
        if openai_key:
            set_secret("openai_api_key", openai_key)
        if serper_key:
            set_secret("serper_api_key", serper_key)
            
        QMessageBox.information(self, "Settings", "Keys saved securely.")
        self.accept()
