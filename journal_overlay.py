"""
Xayk Noob's Journal - Journal Mode Overlay
Interactive overlay with categories, timestamps, and export
"""

import sys
import os
from datetime import datetime
from typing import Optional, List, Dict, Callable
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QScrollArea, QCheckBox, QFrame,
    QLineEdit, QSystemTrayIcon, QMenu, QComboBox, QFileDialog
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPoint
from PyQt6.QtGui import QFont, QCursor, QAction


class JournalItem(QWidget):
    """Single item in the journal with checkbox and timestamp"""
    
    checked_changed = pyqtSignal(str, bool)
    delete_requested = pyqtSignal(str, str)  # text, type
    
    TYPE_COLORS = {
        "item": "#44aaff",
        "location": "#ffaa44",
        "objective": "#44ff44",
        "note": "#aaaaaa",
    }
    
    TYPE_ICONS = {
        "item": "[ITEM]",
        "location": "[LOC]",
        "objective": "[OBJ]",
        "note": "[NOTE]",
    }
    
    def __init__(self, text: str, item_type: str = "note", checked: bool = False, timestamp: str = ""):
        super().__init__()
        self.item_text = text
        self.item_type = item_type
        self.timestamp = timestamp or datetime.now().strftime("%H:%M")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 3, 0, 3)
        layout.setSpacing(6)
        
        # Checkbox
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(checked)
        self.checkbox.setStyleSheet("""
            QCheckBox::indicator {
                width: 12px;
                height: 12px;
                border: 1px solid #00ff00;
                background-color: #0a0a0a;
            }
            QCheckBox::indicator:checked {
                background-color: #00ff00;
            }
        """)
        self.checkbox.stateChanged.connect(self._on_check)
        layout.addWidget(self.checkbox)
        
        # Timestamp
        time_label = QLabel(self.timestamp)
        time_label.setStyleSheet("color: #555555; font-size: 9px; font-family: 'Consolas', monospace;")
        time_label.setFixedWidth(32)
        layout.addWidget(time_label)
        
        # Type tag
        color = self.TYPE_COLORS.get(item_type, "#888888")
        type_label = QLabel(self.TYPE_ICONS.get(item_type, "[?]"))
        type_label.setStyleSheet(f"color: {color}; font-size: 8px; font-family: 'Consolas', monospace;")
        type_label.setFixedWidth(36)
        layout.addWidget(type_label)
        
        # Text
        self.text_label = QLabel(text)
        self.text_label.setStyleSheet("""
            color: #00ff00;
            font-family: 'Consolas', monospace;
            font-size: 11px;
        """)
        self.text_label.setWordWrap(True)
        layout.addWidget(self.text_label, 1)
        
        # Delete button
        delete_btn = QPushButton("x")
        delete_btn.setFixedSize(16, 16)
        delete_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #663333;
                border: none;
                font-size: 10px;
            }
            QPushButton:hover {
                color: #ff4444;
            }
        """)
        delete_btn.clicked.connect(lambda: self.delete_requested.emit(self.item_text, self.item_type))
        layout.addWidget(delete_btn)
        
        if checked:
            self._apply_checked_style()
    
    def _on_check(self, state):
        checked = state == Qt.CheckState.Checked.value
        self.checked_changed.emit(self.item_text, checked)
        if checked:
            self._apply_checked_style()
        else:
            self.text_label.setStyleSheet("""
                color: #00ff00;
                font-family: 'Consolas', monospace;
                font-size: 11px;
            """)
    
    def _apply_checked_style(self):
        self.text_label.setStyleSheet("""
            color: #006600;
            font-family: 'Consolas', monospace;
            font-size: 11px;
            text-decoration: line-through;
        """)


class JournalOverlay(QWidget):
    """Journal mode overlay with categories, timestamps, and export"""
    
    RETRO_GREEN = "rgb(57, 255, 20)"
    RETRO_BG = "rgba(5, 15, 5, 240)"
    RETRO_BORDER = "rgba(57, 255, 20, 100)"
    
    item_checked = pyqtSignal(str, str, bool)  # text, type, checked
    note_added = pyqtSignal(str, str)  # text, type
    note_deleted = pyqtSignal(str, str)  # text, type
    
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
        self._items: Dict[str, JournalItem] = {}
        self._current_filter = "all"
        
        self._setup_ui()
        self._set_default_position()
    
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Main container
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
        container_layout.setContentsMargins(10, 8, 10, 8)
        container_layout.setSpacing(5)
        
        # Header
        header = QHBoxLayout()
        
        title = QLabel("JOURNAL")
        title.setStyleSheet(f"""
            color: {self.RETRO_GREEN};
            font-family: 'Consolas', monospace;
            font-size: 11px;
            font-weight: bold;
            letter-spacing: 2px;
        """)
        header.addWidget(title)
        
        header.addStretch()
        
        # Current task label
        self.task_label = QLabel("")
        self.task_label.setStyleSheet("color: #888888; font-size: 10px;")
        header.addWidget(self.task_label)
        
        header.addStretch()
        
        # Export button
        export_btn = QPushButton("Export")
        export_btn.setFixedHeight(18)
        export_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #666666;
                border: 1px solid #444444;
                font-size: 9px;
                padding: 0 6px;
                font-family: 'Consolas', monospace;
            }
            QPushButton:hover { color: #00ff00; border-color: #00ff00; }
        """)
        export_btn.clicked.connect(self._export_notes)
        header.addWidget(export_btn)
        
        # Minimize button
        min_btn = QPushButton("─")
        min_btn.setFixedSize(18, 18)
        min_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        min_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: rgba(57, 255, 20, 150);
                border: none;
                font-size: 12px;
            }
            QPushButton:hover { color: rgb(57, 255, 20); }
        """)
        min_btn.clicked.connect(self.toggle_minimize)
        header.addWidget(min_btn)
        
        # Close button
        close_btn = QPushButton("x")
        close_btn.setFixedSize(18, 18)
        close_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: rgba(57, 255, 20, 150);
                border: none;
                font-size: 14px;
            }
            QPushButton:hover { color: rgb(57, 255, 20); }
        """)
        close_btn.clicked.connect(self.hide)
        header.addWidget(close_btn)
        
        container_layout.addLayout(header)
        
        # Category filter bar
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(4)
        
        self.filter_buttons = {}
        filters = [
            ("all", "ALL"),
            ("note", "NOTES"),
            ("item", "ITEMS"),
            ("location", "LOCS"),
            ("objective", "OBJS"),
        ]
        
        for filter_key, filter_label in filters:
            btn = QPushButton(filter_label)
            btn.setFixedHeight(18)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.clicked.connect(lambda checked, k=filter_key: self._set_filter(k))
            filter_layout.addWidget(btn)
            self.filter_buttons[filter_key] = btn
        
        filter_layout.addStretch()
        container_layout.addLayout(filter_layout)
        self._update_filter_styles()
        
        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background-color: rgba(57, 255, 20, 50); max-height: 1px;")
        container_layout.addWidget(sep)
        
        # Scroll area for items
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #0a0a0a;
                width: 8px;
            }
            QScrollBar::handle:vertical {
                background-color: #00ff00;
                min-height: 20px;
            }
        """)
        scroll.setMaximumHeight(300)
        
        self.items_widget = QWidget()
        self.items_layout = QVBoxLayout(self.items_widget)
        self.items_layout.setContentsMargins(0, 0, 0, 0)
        self.items_layout.setSpacing(1)
        self.items_layout.addStretch()
        
        scroll.setWidget(self.items_widget)
        container_layout.addWidget(scroll)
        
        # Add note input with type selector
        input_layout = QHBoxLayout()
        input_layout.setSpacing(4)
        
        # Type selector
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Note", "Item", "Location", "Objective"])
        self.type_combo.setFixedWidth(80)
        self.type_combo.setStyleSheet("""
            QComboBox {
                background-color: #0a0a0a;
                color: #888888;
                border: 1px solid #333333;
                padding: 4px;
                font-size: 9px;
                font-family: 'Consolas', monospace;
            }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView {
                background-color: #0a0a0a;
                color: #00ff00;
                selection-background-color: #003300;
            }
        """)
        input_layout.addWidget(self.type_combo)
        
        self.note_input = QLineEdit()
        self.note_input.setPlaceholderText("Add note...")
        self.note_input.setStyleSheet("""
            QLineEdit {
                background-color: #0a0a0a;
                color: #00ff00;
                border: 1px solid #333333;
                padding: 5px;
                font-family: 'Consolas', monospace;
                font-size: 10px;
            }
            QLineEdit:focus {
                border-color: #00ff00;
            }
        """)
        self.note_input.returnPressed.connect(self._add_manual_note)
        input_layout.addWidget(self.note_input)
        
        add_btn = QPushButton("+")
        add_btn.setFixedSize(24, 24)
        add_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #003300;
                color: #00ff00;
                border: 1px solid #00ff00;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #004400;
            }
        """)
        add_btn.clicked.connect(self._add_manual_note)
        input_layout.addWidget(add_btn)
        
        container_layout.addLayout(input_layout)
        
        # Status bar
        status_layout = QHBoxLayout()
        self.status_dot = QLabel("●")
        self.status_dot.setStyleSheet("color: #00ff00; font-size: 6px;")
        status_layout.addWidget(self.status_dot)
        
        self.status_label = QLabel("READY")
        self.status_label.setStyleSheet("color: rgba(57, 255, 20, 150); font-size: 9px;")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        
        self.count_label = QLabel("0 items")
        self.count_label.setStyleSheet("color: #888888; font-size: 9px;")
        status_layout.addWidget(self.count_label)
        
        container_layout.addLayout(status_layout)
        
        # Minimized bar
        self.mini_bar = QWidget()
        self.mini_bar.setStyleSheet("""
            background-color: rgba(5, 15, 5, 180);
            border: 1px solid rgba(57, 255, 20, 60);
        """)
        self.mini_bar.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        mini_layout = QHBoxLayout(self.mini_bar)
        mini_layout.setContentsMargins(10, 5, 10, 5)
        
        self.mini_dot = QLabel("●")
        self.mini_dot.setStyleSheet("color: #00ff00; font-size: 8px;")
        mini_layout.addWidget(self.mini_dot)
        
        mini_title = QLabel("Xayk Noob's Journal")
        mini_title.setStyleSheet("color: rgba(57, 255, 20, 150); font-size: 12px; font-weight: bold;")
        mini_layout.addWidget(mini_title)
        
        self.mini_count = QLabel("(0)")
        self.mini_count.setStyleSheet("color: #888888; font-size: 10px;")
        mini_layout.addWidget(self.mini_count)
        
        self.mini_bar.hide()
        
        main_layout.addWidget(self.container)
        main_layout.addWidget(self.mini_bar)
        
        self.setMinimumSize(350, 180)
        self.setMaximumWidth(450)
    
    def _update_filter_styles(self):
        """Update filter button styles based on active filter"""
        for key, btn in self.filter_buttons.items():
            if key == self._current_filter:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #003300;
                        color: #00ff00;
                        border: 1px solid #00ff00;
                        font-size: 8px;
                        padding: 0 5px;
                        font-family: 'Consolas', monospace;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                        color: #555555;
                        border: 1px solid #333333;
                        font-size: 8px;
                        padding: 0 5px;
                        font-family: 'Consolas', monospace;
                    }
                    QPushButton:hover { color: #00ff00; border-color: #00ff00; }
                """)
    
    def _set_filter(self, filter_key: str):
        """Set the active category filter"""
        self._current_filter = filter_key
        self._update_filter_styles()
        self._apply_filter()
    
    def _apply_filter(self):
        """Show/hide items based on the current filter"""
        for key, item in self._items.items():
            if self._current_filter == "all":
                item.show()
            else:
                item.setVisible(item.item_type == self._current_filter)
    
    def _set_default_position(self):
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            self.move(geo.width() - self.width() - 20, 50)
    
    def toggle_minimize(self):
        if self._is_minimized:
            self._expand()
        else:
            self._minimize()
    
    def _minimize(self):
        self._is_minimized = True
        self.container.hide()
        self.mini_bar.show()
        self.setMinimumSize(0, 0)
        self.adjustSize()
    
    def _expand(self):
        self._is_minimized = False
        self.mini_bar.hide()
        self.container.show()
        self.setMinimumSize(350, 180)
        self.adjustSize()
    
    def add_item(self, text: str, item_type: str = "note", checked: bool = False):
        """Add an item to the journal"""
        key = f"{item_type}:{text.lower()}"
        
        if key in self._items:
            return  # Already exists
        
        item = JournalItem(text, item_type, checked)
        item.checked_changed.connect(lambda t, c: self.item_checked.emit(t, item_type, c))
        item.delete_requested.connect(self._delete_item)
        
        # Insert before the stretch
        self.items_layout.insertWidget(self.items_layout.count() - 1, item)
        self._items[key] = item
        
        self._update_count()
        self._apply_filter()
        
        # Flash effect
        self.mini_dot.setStyleSheet("color: yellow; font-size: 8px;")
        QTimer.singleShot(300, lambda: self.mini_dot.setStyleSheet("color: #00ff00; font-size: 8px;"))
    
    def _delete_item(self, text: str, item_type: str):
        """Delete an item from the journal"""
        key = f"{item_type}:{text.lower()}"
        if key in self._items:
            item = self._items[key]
            self.items_layout.removeWidget(item)
            item.deleteLater()
            del self._items[key]
            self._update_count()
            self.note_deleted.emit(text, item_type)
    
    def add_objective(self, text: str, checked: bool = False):
        self.add_item(text, "objective", checked)
    
    def add_location(self, text: str, checked: bool = False):
        self.add_item(text, "location", checked)
    
    def add_note(self, text: str):
        self.add_item(text, "note", False)
    
    def _add_manual_note(self):
        text = self.note_input.text().strip()
        if text:
            type_map = {"Note": "note", "Item": "item", "Location": "location", "Objective": "objective"}
            note_type = type_map.get(self.type_combo.currentText(), "note")
            self.add_item(text, note_type)
            self.note_added.emit(text, note_type)
            self.note_input.clear()
    
    def _export_notes(self):
        """Export all notes to a text file"""
        if not self._items:
            return
        
        # Build export text
        lines = []
        lines.append("=" * 50)
        lines.append("XAYK NOOB'S JOURNAL - EXPORTED NOTES")
        lines.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append("=" * 50)
        
        # Group by type
        categories = {"objective": "OBJECTIVES", "item": "ITEMS", "location": "LOCATIONS", "note": "NOTES"}
        
        for cat_key, cat_name in categories.items():
            cat_items = [(k, v) for k, v in self._items.items() if v.item_type == cat_key]
            if cat_items:
                lines.append(f"\n--- {cat_name} ---")
                for key, item in cat_items:
                    status = "[x]" if item.checkbox.isChecked() else "[ ]"
                    lines.append(f"  {status} {item.timestamp} {item.item_text}")
        
        lines.append(f"\nTotal: {len(self._items)} entries")
        lines.append("=" * 50)
        
        export_text = "\n".join(lines)
        
        # Save to file
        try:
            export_dir = Path("exports")
            export_dir.mkdir(exist_ok=True)
            filename = f"journal_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            filepath = export_dir / filename
            filepath.write_text(export_text, encoding='utf-8')
            print(f"Notes exported to: {filepath}")
            self.set_status(f"Exported: {filename}", True)
        except Exception as e:
            print(f"Export error: {e}")
    
    def set_current_task(self, task: str):
        self.task_label.setText(task[:40] + "..." if len(task) > 40 else task)
    
    def set_status(self, text: str, active: bool = True):
        self.status_label.setText(text.upper())
        color = "#00ff00" if active else "#ff5555"
        self.status_dot.setStyleSheet(f"color: {color}; font-size: 6px;")
    
    def _update_count(self):
        count = len(self._items)
        checked = sum(1 for item in self._items.values() if item.checkbox.isChecked())
        
        # Count by type
        type_counts = {}
        for item in self._items.values():
            type_counts[item.item_type] = type_counts.get(item.item_type, 0) + 1
        
        summary_parts = []
        for t, c in sorted(type_counts.items()):
            summary_parts.append(f"{c} {t}s")
        
        self.count_label.setText(f"{checked}/{count} done" + (f" ({', '.join(summary_parts)})" if summary_parts else ""))
        self.mini_count.setText(f"({checked}/{count})")
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self._is_minimized:
                self._expand()
                return
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
    
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
    
    def mouseReleaseEvent(self, event):
        self._drag_pos = None
    
    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle_minimize()


class JournalApp:
    """Application wrapper for Journal overlay"""
    
    def __init__(self):
        self.app = QApplication.instance()
        if self.app is None:
            self.app = QApplication(sys.argv)
        
        self.app.setQuitOnLastWindowClosed(False)
        
        self.overlay = JournalOverlay()
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
        
        show_action = QAction("Show Journal", self.app)
        show_action.triggered.connect(self.overlay.show)
        menu.addAction(show_action)
        
        hide_action = QAction("Hide Journal", self.app)
        hide_action.triggered.connect(self.overlay.hide)
        menu.addAction(hide_action)
        
        menu.addSeparator()
        
        export_action = QAction("Export Notes", self.app)
        export_action.triggered.connect(self.overlay._export_notes)
        menu.addAction(export_action)
        
        menu.addSeparator()
        
        quit_action = QAction("Quit", self.app)
        quit_action.triggered.connect(self.quit)
        menu.addAction(quit_action)
        
        self.tray.setContextMenu(menu)
        self.tray.show()
        
        self.tray.activated.connect(self._on_tray_click)
    
    def _on_tray_click(self, reason):
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
                    if isinstance(result, tuple) and len(result) == 2:
                        item_type, text = result
                        if item_type in ["item", "location", "objective"]:
                            self.overlay.add_item(text, item_type)
                        else:
                            self.overlay.set_current_task(text)
            except Exception as e:
                print(f"Update error: {e}")
    
    def start_monitoring(self, interval_ms: int = 10000):
        self.update_timer.start(interval_ms)
        self.overlay.set_status("TRACKING...", True)
    
    def stop_monitoring(self):
        self.update_timer.stop()
        self.overlay.set_status("PAUSED", False)
    
    def quit(self):
        self.update_timer.stop()
        self.tray.hide()
        self.app.quit()
    
    def run(self):
        self.overlay.show()
        return self.app.exec()


if __name__ == "__main__":
    app = JournalApp()
    
    # Add test items
    app.overlay.add_item("M9 Tranquilizer", "item")
    app.overlay.add_item("Ration x3", "item")
    app.overlay.add_location("Tanker - Deck A")
    app.overlay.add_location("Tanker - Engine Room")
    app.overlay.add_objective("Find the Metal Gear RAY")
    app.overlay.add_objective("Take photos of RAY", checked=True)
    app.overlay.add_note("Guards patrol every 30 seconds")
    app.overlay.add_note("Save before boss fight")
    
    app.overlay.set_current_task("Playing: MGS2")
    
    sys.exit(app.run())
