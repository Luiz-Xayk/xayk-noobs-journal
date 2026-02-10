import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, 
    QLabel, QLineEdit, QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QDesktopServices
from PyQt6.QtCore import QUrl


class ConfigDialog(QDialog):
    """First-run configuration dialog for API key setup"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Xayk Noob's Journal - Setup")
        self.setFixedSize(500, 300)
        self.setStyleSheet("""
            QDialog {
                background-color: #1a1a1a;
            }
            QLabel {
                color: #00ff00;
                font-family: 'Consolas', 'Courier New', monospace;
            }
            QLineEdit {
                background-color: #0a0a0a;
                color: #00ff00;
                border: 1px solid #00ff00;
                padding: 8px;
                font-family: 'Consolas', monospace;
                font-size: 12px;
            }
            QPushButton {
                background-color: #0a0a0a;
                color: #00ff00;
                border: 1px solid #00ff00;
                padding: 10px 20px;
                font-family: 'Consolas', monospace;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #002200;
            }
        """)
        
        self.api_key = None
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title = QLabel("XAYK NOOB'S JOURNAL")
        title.setFont(QFont("Consolas", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("First-time Setup")
        subtitle.setStyleSheet("color: #008800; font-size: 11px;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)
        
        layout.addSpacing(10)
        
        # Instructions
        instructions = QLabel(
            "To use this app, you need a free Gemini API key.\n"
            "Click the button below to get your key, then paste it here."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("color: #aaaaaa; font-size: 11px;")
        layout.addWidget(instructions)
        
        # Get API Key button
        get_key_btn = QPushButton("Get Free API Key (opens browser)")
        get_key_btn.clicked.connect(self._open_api_page)
        layout.addWidget(get_key_btn)
        
        layout.addSpacing(5)
        
        # API Key input
        key_label = QLabel("Paste your API key here:")
        key_label.setStyleSheet("font-size: 11px;")
        layout.addWidget(key_label)
        
        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("AIza...")
        self.key_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.key_input)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("Save and Start")
        self.save_btn.clicked.connect(self._save_config)
        btn_layout.addWidget(self.save_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("""
            QPushButton {
                border-color: #555555;
                color: #888888;
            }
            QPushButton:hover {
                background-color: #222222;
            }
        """)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
    
    def _open_api_page(self):
        QDesktopServices.openUrl(QUrl("https://aistudio.google.com/app/apikey"))
    
    def _save_config(self):
        key = self.key_input.text().strip()
        
        if not key:
            QMessageBox.warning(self, "Error", "Please enter an API key.")
            return
        
        if not key.startswith("AIza"):
            QMessageBox.warning(
                self, "Error", 
                "Invalid API key format.\nGemini keys start with 'AIza...'"
            )
            return
        
        # Save to .env file
        env_path = Path(".env")
        env_content = f"""# Xayk Noob's Journal - Configuration
LLM_PROVIDER=gemini
GEMINI_API_KEY={key}
MODE=passive
"""
        
        try:
            env_path.write_text(env_content)
            self.api_key = key
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save config:\n{e}")
    
    def get_api_key(self) -> str:
        return self.api_key


def check_and_configure():
    """Check if API key exists, show config dialog if not"""
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("GEMINI_API_KEY")
    
    # Check if key is valid (not placeholder)
    if api_key and api_key != "your_gemini_api_key_here" and api_key.startswith("AIza"):
        return True
    
    # Show config dialog
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    dialog = ConfigDialog()
    result = dialog.exec()
    
    if result == QDialog.DialogCode.Accepted:
        # Reload environment
        load_dotenv(override=True)
        return True
    
    return False


if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = ConfigDialog()
    if dialog.exec() == QDialog.DialogCode.Accepted:
        print(f"API Key saved!")
    else:
        print("Cancelled")
