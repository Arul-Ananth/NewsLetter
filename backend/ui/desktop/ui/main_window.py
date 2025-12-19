from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel, QLineEdit, QTextEdit, QPushButton, QToolBar, QMessageBox
)
from PySide6.QtGui import QAction
from qasync import asyncSlot
from backend.ui.desktop.ui.settings_dialog import SettingsDialog
from backend.server.services.newsletter_service import newsletter_service

class MainWindow(QMainWindow):
    def __init__(self, user_id: int):
        super().__init__()
        self.user_id = user_id
        self.setWindowTitle("AeroBrief AI Newsletter")
        self.resize(900, 700)
        
        # Toolbar
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)
        
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.open_settings)
        toolbar.addAction(settings_action)

        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Inputs
        layout.addWidget(QLabel("Newsletter Topic:"))
        self.topic_input = QLineEdit()
        self.topic_input.setPlaceholderText("e.g. AI Agents in 2025")
        layout.addWidget(self.topic_input)
        
        layout.addWidget(QLabel("Context / Instructions:"))
        self.context_input = QTextEdit()
        self.context_input.setPlaceholderText("Enter extra context or focus areas...")
        self.context_input.setMaximumHeight(100)
        layout.addWidget(self.context_input)
        
        # Generate Button
        self.generate_btn = QPushButton("Generate Newsletter")
        self.generate_btn.clicked.connect(self.start_generation)
        layout.addWidget(self.generate_btn)
        
        # Output Area
        layout.addWidget(QLabel("Output:"))
        self.output_area = QTextEdit()
        self.output_area.setReadOnly(True)
        layout.addWidget(self.output_area)

    def open_settings(self):
        dlg = SettingsDialog(self)
        dlg.exec()

    @asyncSlot()
    async def start_generation(self):
        topic = self.topic_input.text().strip()
        context = self.context_input.toPlainText().strip()
        
        if not topic:
            self.output_area.setText("Please enter a topic.")
            return

        self.generate_btn.setEnabled(False)
        self.output_area.setText(f"Starting research on '{topic}'... This may take a minute.")
        
        try:
            # Direct Service Call (Async)
            # Context is currently unused in the simplified service but passed if needed later
            result = await newsletter_service.generate_newsletter(topic, self.user_id)
            
            # Update UI
            self.output_area.setMarkdown(result.content)
            
        except Exception as e:
            self.output_area.setText(f"Error occurred: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.generate_btn.setEnabled(True)
