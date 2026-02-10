import sys
from typing import Optional, Callable
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, 
    QHBoxLayout, QPushButton, QSystemTrayIcon, QMenu
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPoint
from PyQt6.QtGui import QFont, QColor, QPalette, QIcon, QAction, QCursor


class TaskOverlay(QWidget):
    """Retro CRT terminal style overlay"""
    
    closed = pyqtSignal()
    
    # Retro colors (phosphorescent green terminal style)
    RETRO_GREEN = "rgb(57, 255, 20)"
    RETRO_GREEN_DIM = "rgba(57, 255, 20, 150)"
    RETRO_GREEN_DARK = "rgba(20, 80, 20, 200)"
    RETRO_BG = "rgba(5, 15, 5, 235)"
    RETRO_BG_MINI = "rgba(5, 15, 5, 160)"
    RETRO_BORDER = "rgba(57, 255, 20, 100)"
    RETRO_BORDER_MINI = "rgba(57, 255, 20, 60)"
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("Xayk Noob's Journal")
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool
        )
        
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self._drag_pos: Optional[QPoint] = None
        self._is_minimized = False
        self._pending_task: Optional[tuple] = None
        
        self._setup_ui()
        self._set_default_position()
        
        self._auto_hide_timer = QTimer()
        self._auto_hide_timer.setSingleShot(True)
        self._auto_hide_timer.timeout.connect(self._fade_out)
        
    def _setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # === MAIN CONTAINER (expanded) ===
        self.container = QWidget()
        self.container.setObjectName("container")
        self.container.setStyleSheet(f"""
            #container {{
                background-color: {self.RETRO_BG};
                border: 1px solid {self.RETRO_BORDER};
                border-radius: 4px;
            }}
        """)
        
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(12, 8, 12, 8)
        container_layout.setSpacing(6)
        
        # Header
        header_layout = QHBoxLayout()
        
        self.title_label = QLabel("► QUEST")
        self.title_label.setStyleSheet(f"""
            QLabel {{
                color: {self.RETRO_GREEN};
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 10px;
                font-weight: bold;
                letter-spacing: 2px;
            }}
        """)
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        # Minimize button
        self.minimize_btn = QPushButton("─")
        self.minimize_btn.setFixedSize(18, 18)
        self.minimize_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.minimize_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {self.RETRO_GREEN_DIM};
                border: none;
                font-family: 'Consolas', monospace;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                color: {self.RETRO_GREEN};
            }}
        """)
        self.minimize_btn.clicked.connect(self.toggle_minimize)
        header_layout.addWidget(self.minimize_btn)
        
        # Close button
        self.close_btn = QPushButton("×")
        self.close_btn.setFixedSize(18, 18)
        self.close_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {self.RETRO_GREEN_DIM};
                border: none;
                font-family: 'Consolas', monospace;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                color: {self.RETRO_GREEN};
            }}
        """)
        self.close_btn.clicked.connect(self.hide)
        header_layout.addWidget(self.close_btn)
        
        container_layout.addLayout(header_layout)
        
        # Separator line
        separator = QLabel("─" * 35)
        separator.setStyleSheet(f"""
            QLabel {{
                color: {self.RETRO_GREEN_DIM};
                font-family: 'Consolas', monospace;
                font-size: 8px;
            }}
        """)
        container_layout.addWidget(separator)
        
        # Task text
        self.task_label = QLabel("Waiting for task...")
        self.task_label.setWordWrap(True)
        self.task_label.setMinimumWidth(260)
        self.task_label.setMaximumWidth(350)
        self.task_label.setStyleSheet(f"""
            QLabel {{
                color: {self.RETRO_GREEN};
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 13px;
                padding: 4px 0px;
                line-height: 1.3;
            }}
        """)
        container_layout.addWidget(self.task_label)
        
        # Context label
        self.context_label = QLabel("")
        self.context_label.setWordWrap(True)
        self.context_label.setStyleSheet(f"""
            QLabel {{
                color: {self.RETRO_GREEN_DIM};
                font-family: 'Consolas', monospace;
                font-size: 10px;
            }}
        """)
        self.context_label.hide()
        container_layout.addWidget(self.context_label)
        
        # Status
        self.status_layout = QHBoxLayout()
        
        self.status_dot = QLabel("●")
        self.status_dot.setStyleSheet(f"color: {self.RETRO_GREEN}; font-size: 6px;")
        self.status_layout.addWidget(self.status_dot)
        
        self.status_label = QLabel("SCANNING...")
        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: {self.RETRO_GREEN_DIM};
                font-family: 'Consolas', monospace;
                font-size: 9px;
                letter-spacing: 1px;
            }}
        """)
        self.status_layout.addWidget(self.status_label)
        self.status_layout.addStretch()
        
        container_layout.addLayout(self.status_layout)
        
        # === MINIMIZED CONTAINER ===
        self.mini_container = QWidget()
        self.mini_container.setObjectName("mini_container")
        self.mini_container.setStyleSheet(f"""
            #mini_container {{
                background-color: {self.RETRO_BG_MINI};
                border: 1px solid {self.RETRO_BORDER_MINI};
                border-radius: 3px;
            }}
        """)
        self.mini_container.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        mini_layout = QHBoxLayout(self.mini_container)
        mini_layout.setContentsMargins(12, 6, 12, 6)
        
        self.mini_dot = QLabel("●")
        self.mini_dot.setStyleSheet(f"color: {self.RETRO_GREEN}; font-size: 8px;")
        mini_layout.addWidget(self.mini_dot)
        
        self.mini_label = QLabel("Xayk Noob's Journal")
        self.mini_label.setStyleSheet(f"""
            QLabel {{
                color: {self.RETRO_GREEN_DIM};
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
                letter-spacing: 1px;
            }}
        """)
        mini_layout.addWidget(self.mini_label)
        
        # New task indicator when minimized
        self.mini_new_indicator = QLabel("●")
        self.mini_new_indicator.setStyleSheet("color: rgba(255, 200, 50, 200); font-size: 8px;")
        self.mini_new_indicator.hide()
        mini_layout.addWidget(self.mini_new_indicator)
        
        self.mini_container.hide()
        
        # Adiciona containers ao layout principal
        self.main_layout.addWidget(self.container)
        self.main_layout.addWidget(self.mini_container)
        
        self.setMinimumSize(280, 80)
        self.adjustSize()
    
    def _set_default_position(self):
        screen = QApplication.primaryScreen()
        if screen:
            geometry = screen.availableGeometry()
            x = geometry.width() - self.width() - 20
            y = 50
            self.move(x, y)
    
    def toggle_minimize(self):
        """Toggle between expanded and minimized mode"""
        if self._is_minimized:
            self._expand()
        else:
            self._minimize()
    
    def _minimize(self):
        """Minimize the overlay"""
        self._is_minimized = True
        self.container.hide()
        self.mini_container.show()
        self.setMinimumSize(0, 0)
        self.adjustSize()
        
        # Show indicator if pending task
        if self._pending_task:
            self.mini_new_indicator.show()
    
    def _expand(self):
        """Expand the overlay"""
        self._is_minimized = False
        self.mini_container.hide()
        self.container.show()
        self.mini_new_indicator.hide()
        self.setMinimumSize(280, 80)
        self.adjustSize()
        
        # Apply pending task if any
        if self._pending_task:
            task_text, context = self._pending_task
            self.task_label.setText(task_text)
            if context:
                self.context_label.setText(f"// {context}")
                self.context_label.show()
            else:
                self.context_label.hide()
            self._pending_task = None
    
    def set_task(self, task_text: str, context: Optional[str] = None):
        if self._is_minimized:
            # Store task for when expanded and show indicator
            self._pending_task = (task_text, context)
            self.mini_new_indicator.show()
            # Flash the indicator
            self._flash_mini_indicator()
        else:
            self.task_label.setText(task_text)
            
            if context:
                self.context_label.setText(f"// {context}")
                self.context_label.show()
            else:
                self.context_label.hide()
            
            self.adjustSize()
            self._flash_border()
    
    def _flash_mini_indicator(self):
        """Flash the new task indicator in mini mode"""
        self.mini_new_indicator.setStyleSheet("color: rgba(255, 255, 100, 255); font-size: 8px;")
        QTimer.singleShot(300, lambda: self.mini_new_indicator.setStyleSheet("color: rgba(255, 200, 50, 200); font-size: 8px;"))
    
    def set_status(self, status: str, is_active: bool = True):
        self.status_label.setText(status.upper())
        
        if is_active:
            self.status_dot.setStyleSheet(f"color: {self.RETRO_GREEN}; font-size: 6px;")
            self.mini_dot.setStyleSheet(f"color: {self.RETRO_GREEN}; font-size: 6px;")
        else:
            self.status_dot.setStyleSheet("color: rgba(255, 80, 80, 200); font-size: 6px;")
            self.mini_dot.setStyleSheet("color: rgba(255, 80, 80, 200); font-size: 6px;")
    
    def _flash_border(self):
        """Flash de borda quando nova task aparece"""
        self.container.setStyleSheet(f"""
            #container {{
                background-color: {self.RETRO_BG};
                border: 1px solid {self.RETRO_GREEN};
                border-radius: 4px;
            }}
        """)
        
        QTimer.singleShot(150, self._reset_border)
    
    def _reset_border(self):
        self.container.setStyleSheet(f"""
            #container {{
                background-color: {self.RETRO_BG};
                border: 1px solid {self.RETRO_BORDER};
                border-radius: 4px;
            }}
        """)
    
    def _fade_out(self):
        self.hide()
    
    def enable_auto_hide(self, seconds: int = 30):
        self._auto_hide_timer.start(seconds * 1000)
    
    def disable_auto_hide(self):
        self._auto_hide_timer.stop()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # If clicked on mini container, expand
            if self._is_minimized:
                mini_rect = self.mini_container.geometry()
                if mini_rect.contains(event.pos()):
                    self._expand()
                    return
            
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
    
    def mouseReleaseEvent(self, event):
        self._drag_pos = None
    
    def mouseDoubleClickEvent(self, event):
        """Double-click toggles minimize"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle_minimize()


class RetroTaskerApp:
    
    def __init__(self):
        self.app = QApplication.instance()
        if self.app is None:
            self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        
        self.overlay = TaskOverlay()
        
        self._setup_tray()
        
        self._update_callback: Optional[Callable] = None
        
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._on_update)
    
    def _setup_tray(self):
        self.tray = QSystemTrayIcon()
        
        self.tray.setIcon(self.app.style().standardIcon(
            self.app.style().StandardPixmap.SP_ComputerIcon
        ))
        self.tray.setToolTip("Xayk Noob's Journal")
        
        menu = QMenu()
        
        show_action = QAction("Show Overlay", self.app)
        show_action.triggered.connect(self.overlay.show)
        menu.addAction(show_action)
        
        hide_action = QAction("Hide Overlay", self.app)
        hide_action.triggered.connect(self.overlay.hide)
        menu.addAction(hide_action)
        
        menu.addSeparator()
        
        minimize_action = QAction("Toggle Minimize", self.app)
        minimize_action.triggered.connect(self.overlay.toggle_minimize)
        menu.addAction(minimize_action)
        
        menu.addSeparator()
        
        quit_action = QAction("Quit", self.app)
        quit_action.triggered.connect(self.quit)
        menu.addAction(quit_action)
        
        self.tray.setContextMenu(menu)
        self.tray.show()
        
        self.tray.activated.connect(self._on_tray_activated)
    
    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            if self.overlay.isVisible():
                self.overlay.hide()
            else:
                self.overlay.show()
    
    def set_update_callback(self, callback: Callable):
        self._update_callback = callback
    
    def _on_update(self):
        if self._update_callback:
            try:
                result = self._update_callback()
                if result:
                    task_text, context = result
                    self.overlay.set_task(task_text, context)
                    self.overlay.set_status("SCANNING...", True)
            except Exception as e:
                self.overlay.set_status(f"ERROR", False)
    
    def start_monitoring(self, interval_ms: int = 3000):
        self.update_timer.start(interval_ms)
        self.overlay.set_status("SCANNING...", True)
    
    def stop_monitoring(self):
        self.update_timer.stop()
        self.overlay.set_status("PAUSED", False)
    
    def show(self):
        self.overlay.show()
    
    def quit(self):
        self.update_timer.stop()
        self.tray.hide()
        self.app.quit()
    
    def run(self):
        self.overlay.show()
        return self.app.exec()


def main():
    print("=" * 50)
    print("Xayk Noob's Journal - Overlay UI Test")
    print("=" * 50)
    
    app = RetroTaskerApp()
    
    test_tasks = [
        ("Go to the Generator Room", "Resident Evil 2 - Laboratory"),
        ("Activate panels in order: Blue -> Red -> Green", None),
        ("Pick up the Heart Key on the desk", "Police Station - Office"),
        ("Defeat G1 by aiming at the eye on the shoulder", "Boss Fight!"),
    ]
    
    task_index = [0]
    
    def get_next_task():
        if task_index[0] < len(test_tasks):
            task = test_tasks[task_index[0]]
            task_index[0] = (task_index[0] + 1) % len(test_tasks)
            return task
        return None
    
    app.set_update_callback(get_next_task)
    app.start_monitoring(interval_ms=5000)
    
    print("\nOverlay started!")
    print("   - Drag to move")
    print("   - Double-click to minimize/expand")
    print("   - Double-click tray icon to show/hide")
    print("   - Right-click tray icon for menu")
    print("\nSample tasks will cycle every 5 seconds")
    
    return app.run()


if __name__ == "__main__":
    sys.exit(main())
