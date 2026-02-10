"""
Xayk Noob's Journal - Launcher
Main menu to select game, mode, and configure settings
"""

import sys
import os
from pathlib import Path
from typing import Optional, List

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QRadioButton, QButtonGroup,
    QGroupBox, QFrame, QStackedWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QCursor


class GameSelector(QGroupBox):
    """Widget for selecting the game"""
    
    game_changed = pyqtSignal(str)
    
    def __init__(self):
        super().__init__("SELECT GAME")
        self.setStyleSheet("""
            QGroupBox {
                color: #00ff00;
                font-family: 'Consolas', monospace;
                font-size: 11px;
                border: 1px solid #00ff00;
                border-radius: 0px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        # Auto-detect label
        self.auto_label = QLabel("Auto-detecting from emulator window...")
        self.auto_label.setStyleSheet("color: #888888; font-size: 10px;")
        layout.addWidget(self.auto_label)
        
        # Game dropdown
        self.game_combo = QComboBox()
        self.game_combo.setStyleSheet("""
            QComboBox {
                background-color: #0a0a0a;
                color: #00ff00;
                border: 1px solid #00ff00;
                padding: 8px;
                font-family: 'Consolas', monospace;
                font-size: 12px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #0a0a0a;
                color: #00ff00;
                selection-background-color: #003300;
            }
        """)
        self.game_combo.currentTextChanged.connect(self.game_changed.emit)
        layout.addWidget(self.game_combo)
        
        # Refresh button
        refresh_btn = QPushButton("Refresh Games")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #00aa00;
                border: none;
                font-size: 10px;
                text-decoration: underline;
            }
            QPushButton:hover {
                color: #00ff00;
            }
        """)
        refresh_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        refresh_btn.clicked.connect(self.refresh_games)
        layout.addWidget(refresh_btn)
        
        self.refresh_games()
    
    def refresh_games(self):
        """Scan guides folder for available games"""
        self.game_combo.clear()
        self.game_combo.addItem("Auto-detect")
        
        guides_path = Path("guides")
        if guides_path.exists():
            for folder in sorted(guides_path.iterdir()):
                if folder.is_dir() and not folder.name.startswith((".", "_", "EXAMPLE")):
                    game_name = folder.name.replace("_", " ")
                    self.game_combo.addItem(game_name)
    
    def get_selected_game(self) -> Optional[str]:
        text = self.game_combo.currentText()
        return None if text == "Auto-detect" else text


class ModeSelector(QGroupBox):
    """Widget for selecting the mode"""
    
    mode_changed = pyqtSignal(str)
    
    def __init__(self):
        super().__init__("SELECT MODE")
        self.setStyleSheet("""
            QGroupBox {
                color: #00ff00;
                font-family: 'Consolas', monospace;
                font-size: 11px;
                border: 1px solid #00ff00;
                border-radius: 0px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        self.button_group = QButtonGroup(self)
        
        # Journal Mode
        journal_layout = QHBoxLayout()
        
        self.journal_radio = QRadioButton()
        self.journal_radio.setChecked(True)
        self.journal_radio.setStyleSheet("""
            QRadioButton::indicator {
                width: 20px;
                height: 20px;
                border: 2px solid #555555;
                border-radius: 3px;
                background-color: #0a0a0a;
            }
            QRadioButton::indicator:checked {
                background-color: #00ff00;
                border-color: #00ff00;
            }
        """)
        self.button_group.addButton(self.journal_radio)
        journal_layout.addWidget(self.journal_radio)
        
        journal_text_layout = QVBoxLayout()
        journal_text_layout.setSpacing(2)
        
        journal_title = QLabel("JOURNAL MODE")
        journal_title.setStyleSheet("""
            color: #ffffff;
            font-family: 'Consolas', monospace;
            font-size: 15px;
            font-weight: bold;
        """)
        journal_text_layout.addWidget(journal_title)
        
        journal_desc = QLabel("Track your progress with checkboxes. No spoilers.")
        journal_desc.setStyleSheet("color: #888888; font-size: 11px;")
        journal_desc.setWordWrap(True)
        journal_text_layout.addWidget(journal_desc)
        
        journal_layout.addLayout(journal_text_layout)
        journal_layout.addStretch()
        
        layout.addLayout(journal_layout)
        
        # Separator line
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background-color: #333333; max-height: 1px;")
        layout.addWidget(sep)
        
        # Guide Mode
        guide_layout = QHBoxLayout()
        
        self.guide_radio = QRadioButton()
        self.guide_radio.setStyleSheet("""
            QRadioButton::indicator {
                width: 20px;
                height: 20px;
                border: 2px solid #555555;
                border-radius: 3px;
                background-color: #0a0a0a;
            }
            QRadioButton::indicator:checked {
                background-color: #00ff00;
                border-color: #00ff00;
            }
        """)
        self.button_group.addButton(self.guide_radio)
        guide_layout.addWidget(self.guide_radio)
        
        guide_text_layout = QVBoxLayout()
        guide_text_layout.setSpacing(2)
        
        guide_title = QLabel("GUIDE MODE")
        guide_title.setStyleSheet("""
            color: #ffffff;
            font-family: 'Consolas', monospace;
            font-size: 15px;
            font-weight: bold;
        """)
        guide_text_layout.addWidget(guide_title)
        
        guide_desc = QLabel("Get direct instructions when you're stuck.")
        guide_desc.setStyleSheet("color: #888888; font-size: 11px;")
        guide_desc.setWordWrap(True)
        guide_text_layout.addWidget(guide_desc)
        
        guide_layout.addLayout(guide_text_layout)
        guide_layout.addStretch()
        
        layout.addLayout(guide_layout)
        
        self.button_group.buttonClicked.connect(self._on_mode_changed)
    
    def _on_mode_changed(self, button):
        mode = "journal" if button == self.journal_radio else "guide"
        self.mode_changed.emit(mode)
    
    def get_selected_mode(self) -> str:
        return "journal" if self.journal_radio.isChecked() else "guide"


class StatusPanel(QFrame):
    """Shows current status"""
    
    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            QFrame {
                background-color: #0a0a0a;
                border: 1px solid #333333;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("STATUS")
        title.setStyleSheet("color: #888888; font-size: 10px;")
        layout.addWidget(title)
        
        self.ollama_status = QLabel("Ollama: Checking...")
        self.ollama_status.setStyleSheet("color: #888888; font-size: 11px;")
        layout.addWidget(self.ollama_status)
        
        self.emulator_status = QLabel("Emulator: Not detected")
        self.emulator_status.setStyleSheet("color: #888888; font-size: 11px;")
        layout.addWidget(self.emulator_status)
        
        self.check_status()
    
    def check_status(self):
        # Check Ollama
        try:
            import subprocess
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            if result.returncode == 0:
                self.ollama_status.setText("Ollama: Ready")
                self.ollama_status.setStyleSheet("color: #00ff00; font-size: 11px;")
            else:
                self.ollama_status.setText("Ollama: Not running")
                self.ollama_status.setStyleSheet("color: #ff5555; font-size: 11px;")
        except:
            self.ollama_status.setText("Ollama: Not installed")
            self.ollama_status.setStyleSheet("color: #ff5555; font-size: 11px;")
    
    def set_emulator(self, name: str):
        if name:
            self.emulator_status.setText(f"Emulator: {name}")
            self.emulator_status.setStyleSheet("color: #00ff00; font-size: 11px;")
        else:
            self.emulator_status.setText("Emulator: Not detected")
            self.emulator_status.setStyleSheet("color: #888888; font-size: 11px;")


class LauncherWindow(QMainWindow):
    """Main launcher window"""
    
    start_requested = pyqtSignal(str, str)  # game, mode
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Xayk Noob's Journal")
        self.setFixedSize(450, 550)
        self.setStyleSheet("background-color: #1a1a1a;")
        
        central = QWidget()
        self.setCentralWidget(central)
        
        layout = QVBoxLayout(central)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("XAYK NOOB'S JOURNAL")
        title.setFont(QFont("Consolas", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #00ff00;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        subtitle = QLabel("AI-Powered Retro Game Assistant")
        subtitle.setStyleSheet("color: #008800; font-size: 11px;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)
        
        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background-color: #333333;")
        layout.addWidget(sep)
        
        # Game selector
        self.game_selector = GameSelector()
        layout.addWidget(self.game_selector)
        
        # Mode selector
        self.mode_selector = ModeSelector()
        layout.addWidget(self.mode_selector)
        
        # Status panel
        self.status_panel = StatusPanel()
        layout.addWidget(self.status_panel)
        
        layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        # Settings button
        settings_btn = QPushButton("Settings")
        settings_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #888888;
                border: 1px solid #555555;
                padding: 10px 20px;
                font-family: 'Consolas', monospace;
            }
            QPushButton:hover {
                border-color: #888888;
                color: #aaaaaa;
            }
        """)
        settings_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_layout.addWidget(settings_btn)
        
        btn_layout.addStretch()
        
        # Start button
        self.start_btn = QPushButton("START")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #003300;
                color: #00ff00;
                border: 2px solid #00ff00;
                padding: 12px 40px;
                font-family: 'Consolas', monospace;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #004400;
            }
        """)
        self.start_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.start_btn.clicked.connect(self._on_start)
        btn_layout.addWidget(self.start_btn)
        
        layout.addLayout(btn_layout)
    
    def _on_start(self):
        game = self.game_selector.get_selected_game()
        mode = self.mode_selector.get_selected_mode()
        self.start_requested.emit(game or "", mode)
        self.hide()


def run_launcher() -> tuple:
    """Run launcher and return (game, mode) selection"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    result = {"game": None, "mode": "journal"}
    
    def on_start(game, mode):
        result["game"] = game if game else None
        result["mode"] = mode
        app.quit()
    
    launcher = LauncherWindow()
    launcher.start_requested.connect(on_start)
    launcher.show()
    
    app.exec()
    
    return result["game"], result["mode"]


if __name__ == "__main__":
    game, mode = run_launcher()
    print(f"Selected: game={game}, mode={mode}")
