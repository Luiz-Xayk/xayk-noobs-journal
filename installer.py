"""
Xayk Noob's Journal - Complete Installer
Downloads and installs everything automatically:
1. Ollama (local LLM runtime)
2. LLaVA model (vision AI)
3. The app itself
"""

import sys
import os
import subprocess
import urllib.request
import shutil
import time
import threading
from pathlib import Path

# Check if running as GUI or CLI
try:
    from PyQt6.QtWidgets import (
        QApplication, QWizard, QWizardPage, QVBoxLayout, QHBoxLayout,
        QLabel, QProgressBar, QPushButton, QTextEdit, QCheckBox
    )
    from PyQt6.QtCore import Qt, QThread, pyqtSignal
    from PyQt6.QtGui import QFont
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False


class InstallWorker(QThread if GUI_AVAILABLE else object):
    """Background worker for installation tasks"""
    
    if GUI_AVAILABLE:
        progress = pyqtSignal(int)
        status = pyqtSignal(str)
        log = pyqtSignal(str)
        finished_signal = pyqtSignal(bool)
    
    def __init__(self):
        if GUI_AVAILABLE:
            super().__init__()
        self.cancelled = False
    
    def run(self):
        try:
            success = self._install()
            if GUI_AVAILABLE:
                self.finished_signal.emit(success)
        except Exception as e:
            if GUI_AVAILABLE:
                self.log.emit(f"Error: {e}")
                self.finished_signal.emit(False)
    
    def _emit_progress(self, value):
        if GUI_AVAILABLE:
            self.progress.emit(value)
    
    def _emit_status(self, text):
        if GUI_AVAILABLE:
            self.status.emit(text)
        print(text)
    
    def _emit_log(self, text):
        if GUI_AVAILABLE:
            self.log.emit(text)
        print(f"  {text}")
    
    def _install(self) -> bool:
        # Step 1: Check/Install Ollama (0-40%)
        self._emit_status("Checking Ollama installation...")
        self._emit_progress(5)
        
        if not self._is_ollama_installed():
            self._emit_status("Downloading Ollama...")
            self._emit_log("Ollama not found, downloading...")
            
            if not self._download_ollama():
                self._emit_log("Failed to download Ollama")
                return False
            
            self._emit_progress(20)
            self._emit_status("Installing Ollama...")
            
            if not self._install_ollama():
                self._emit_log("Failed to install Ollama")
                return False
        else:
            self._emit_log("Ollama already installed")
        
        self._emit_progress(40)
        
        # Step 2: Start Ollama service (40-50%)
        self._emit_status("Starting Ollama service...")
        self._start_ollama_service()
        self._emit_progress(50)
        
        # Step 3: Download LLaVA model (50-90%)
        self._emit_status("Downloading AI model (this may take a while)...")
        self._emit_log("Pulling llava model (~4GB)...")
        
        if not self._pull_model("llava"):
            # Try smaller model as fallback
            self._emit_log("LLaVA failed, trying smaller model...")
            if not self._pull_model("llava:7b"):
                self._emit_log("Failed to download AI model")
                return False
        
        self._emit_progress(90)
        
        # Step 4: Create config (90-100%)
        self._emit_status("Finalizing installation...")
        self._create_config()
        self._emit_progress(100)
        
        self._emit_status("Installation complete!")
        self._emit_log("Ready to use!")
        return True
    
    def _is_ollama_installed(self) -> bool:
        """Check if Ollama is installed"""
        # Check common installation paths on Windows
        if os.name == 'nt':
            common_paths = [
                Path(os.environ.get('LOCALAPPDATA', '')) / 'Programs' / 'Ollama' / 'ollama.exe',
                Path(os.environ.get('PROGRAMFILES', '')) / 'Ollama' / 'ollama.exe',
                Path.home() / 'AppData' / 'Local' / 'Programs' / 'Ollama' / 'ollama.exe',
            ]
            for path in common_paths:
                if path.exists():
                    self._emit_log(f"Found Ollama at: {path}")
                    return True
        
        # Try running the command
        try:
            result = subprocess.run(
                ["ollama", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def _download_ollama(self) -> bool:
        """Download Ollama installer"""
        url = "https://ollama.com/download/OllamaSetup.exe"
        installer_path = Path.home() / "Downloads" / "OllamaSetup.exe"
        
        try:
            self._emit_log(f"Downloading from {url}...")
            urllib.request.urlretrieve(url, installer_path)
            self.ollama_installer = installer_path
            return True
        except Exception as e:
            self._emit_log(f"Download error: {e}")
            return False
    
    def _install_ollama(self) -> bool:
        """Install Ollama silently"""
        if not hasattr(self, 'ollama_installer'):
            return False
        
        try:
            self._emit_log("Running Ollama installer...")
            # Run installer silently
            result = subprocess.run(
                [str(self.ollama_installer), "/VERYSILENT", "/NORESTART"],
                capture_output=True,
                timeout=300  # 5 min timeout
            )
            
            # Wait for installation to complete
            time.sleep(5)
            
            # Verify installation
            return self._is_ollama_installed()
        except Exception as e:
            self._emit_log(f"Install error: {e}")
            return False
    
    def _get_ollama_path(self) -> str:
        """Get the path to ollama executable"""
        if os.name == 'nt':
            common_paths = [
                Path(os.environ.get('LOCALAPPDATA', '')) / 'Programs' / 'Ollama' / 'ollama.exe',
                Path.home() / 'AppData' / 'Local' / 'Programs' / 'Ollama' / 'ollama.exe',
            ]
            for path in common_paths:
                if path.exists():
                    return str(path)
        return "ollama"
    
    def _start_ollama_service(self):
        """Start Ollama service"""
        try:
            ollama_path = self._get_ollama_path()
            self._emit_log(f"Starting Ollama from: {ollama_path}")
            
            # Try to start ollama serve in background
            if os.name == 'nt':
                subprocess.Popen(
                    [ollama_path, "serve"],
                    creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            else:
                subprocess.Popen(
                    [ollama_path, "serve"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            time.sleep(5)  # Wait for service to start
            self._emit_log("Ollama service started")
        except Exception as e:
            self._emit_log(f"Service start warning: {e}")
    
    def _pull_model(self, model_name: str) -> bool:
        """Download AI model"""
        try:
            ollama_path = self._get_ollama_path()
            self._emit_log(f"Pulling {model_name}...")
            
            # Set environment for UTF-8
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            
            process = subprocess.Popen(
                [ollama_path, "pull", model_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=env,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            # Stream output with proper encoding handling
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                if line:
                    try:
                        decoded = line.decode('utf-8', errors='ignore').strip()
                    except:
                        decoded = line.decode('latin-1', errors='ignore').strip()
                    
                    if decoded:
                        # Show progress
                        if "pulling" in decoded.lower() or "%" in decoded or "success" in decoded.lower() or "download" in decoded.lower():
                            self._emit_log(decoded)
            
            process.wait()
            
            if process.returncode == 0:
                self._emit_log(f"{model_name} downloaded successfully!")
                return True
            else:
                self._emit_log(f"Pull failed with code: {process.returncode}")
                return False
            
        except Exception as e:
            self._emit_log(f"Model pull error: {e}")
            return False
    
    def _create_config(self):
        """Create app configuration"""
        env_content = """# Xayk Noob's Journal - Configuration
# Auto-configured by installer

LLM_PROVIDER=ollama
MODE=passive
"""
        Path(".env").write_text(env_content)
        self._emit_log("Configuration created")


class WelcomePage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Welcome")
        
        layout = QVBoxLayout(self)
        
        title = QLabel("Xayk Noob's Journal")
        title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        title.setStyleSheet("color: #2d8cf0;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        subtitle = QLabel("AI-Powered Retro Game Assistant")
        subtitle.setFont(QFont("Segoe UI", 11))
        subtitle.setStyleSheet("color: #666666;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)
        
        layout.addSpacing(30)
        
        info = QLabel(
            "This installer will set up everything you need:\n\n"
            "1. Ollama - Local AI runtime\n"
            "2. LLaVA - Vision AI model (~4GB download)\n"
            "3. App configuration\n\n"
            "The AI runs completely on your computer.\n"
            "No internet required after installation.\n"
            "No API keys or accounts needed."
        )
        info.setWordWrap(True)
        info.setFont(QFont("Segoe UI", 10))
        info.setStyleSheet("color: #333333; line-height: 1.6;")
        layout.addWidget(info)
        
        layout.addStretch()
        
        warning = QLabel("Note: Installation requires ~5GB of disk space.")
        warning.setFont(QFont("Segoe UI", 9))
        warning.setStyleSheet("color: #ff9800;")
        layout.addWidget(warning)


class InstallPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Installation")
        self.setCommitPage(True)
        
        self.install_complete = False
        self.worker = None
        
        layout = QVBoxLayout(self)
        
        self.status_label = QLabel("Click 'Install' to begin...")
        self.status_label.setFont(QFont("Segoe UI", 11))
        self.status_label.setStyleSheet("color: #2d8cf0;")
        layout.addWidget(self.status_label)
        
        layout.addSpacing(10)
        
        self.progress = QProgressBar()
        self.progress.setFont(QFont("Segoe UI", 9))
        self.progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #cccccc;
                border-radius: 3px;
                background-color: #f0f0f0;
                text-align: center;
                color: #333333;
                height: 22px;
            }
            QProgressBar::chunk {
                background-color: #2d8cf0;
                border-radius: 2px;
            }
        """)
        layout.addWidget(self.progress)
        
        layout.addSpacing(10)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #fafafa;
                color: #333333;
                border: 1px solid #cccccc;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.log_text)
        
        self.install_btn = QPushButton("Install")
        self.install_btn.setFont(QFont("Segoe UI", 11))
        self.install_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d8cf0;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 30px;
            }
            QPushButton:hover {
                background-color: #1a6fcc;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #888888;
            }
        """)
        self.install_btn.clicked.connect(self._start_install)
        layout.addWidget(self.install_btn)
    
    def _start_install(self):
        self.install_btn.setEnabled(False)
        self.log_text.clear()
        
        self.worker = InstallWorker()
        self.worker.progress.connect(self.progress.setValue)
        self.worker.status.connect(self.status_label.setText)
        self.worker.log.connect(self._add_log)
        self.worker.finished_signal.connect(self._on_finished)
        self.worker.start()
    
    def _add_log(self, text):
        self.log_text.append(text)
    
    def _on_finished(self, success):
        self.install_complete = success
        if success:
            self.status_label.setText("Installation complete!")
            self.status_label.setStyleSheet("color: #4caf50;")
        else:
            self.status_label.setText("Installation failed. Check log for details.")
            self.status_label.setStyleSheet("color: #f44336;")
        
        self.completeChanged.emit()
    
    def isComplete(self):
        return self.install_complete


class FinishPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Complete")
        
        layout = QVBoxLayout(self)
        
        layout.addSpacing(20)
        
        success = QLabel("Installation Successful!")
        success.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        success.setStyleSheet("color: #4caf50;")
        success.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(success)
        
        layout.addSpacing(20)
        
        info = QLabel(
            "Xayk Noob's Journal is ready to use!\n\n"
            "How to use:\n"
            "1. Open your game in an emulator\n"
            "2. Run XaykNoobsJournal.exe\n"
            "3. The overlay will show game guidance\n\n"
            "Add game guides to the 'guides/' folder\n"
            "for better results."
        )
        info.setWordWrap(True)
        info.setFont(QFont("Segoe UI", 10))
        info.setStyleSheet("color: #333333;")
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info)
        
        layout.addStretch()
        
        self.launch_check = QCheckBox("Launch Xayk Noob's Journal now")
        self.launch_check.setChecked(True)
        self.launch_check.setFont(QFont("Segoe UI", 10))
        self.launch_check.setStyleSheet("color: #333333;")
        layout.addWidget(self.launch_check)
    
    def should_launch(self):
        return self.launch_check.isChecked()


class InstallerWizard(QWizard):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Xayk Noob's Journal - Setup")
        self.setFixedSize(600, 500)
        
        self.setStyleSheet("""
            QWizard {
                background-color: #ffffff;
            }
            QWizardPage {
                background-color: #ffffff;
            }
            QLabel {
                color: #333333;
            }
            QPushButton {
                font-family: 'Segoe UI';
                font-size: 11px;
                padding: 8px 20px;
                border-radius: 4px;
                background-color: #e0e0e0;
                color: #333333;
                border: 1px solid #cccccc;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #d0d0d0;
            }
            QPushButton:default {
                background-color: #2d8cf0;
                color: white;
                border: none;
            }
            QPushButton:default:hover {
                background-color: #1a6fcc;
            }
        """)
        
        self.addPage(WelcomePage())
        self.install_page = InstallPage()
        self.addPage(self.install_page)
        self.finish_page = FinishPage()
        self.addPage(self.finish_page)
        
        self.setButtonText(QWizard.WizardButton.NextButton, "Next >")
        self.setButtonText(QWizard.WizardButton.BackButton, "< Back")
        self.setButtonText(QWizard.WizardButton.FinishButton, "Finish")
        self.setButtonText(QWizard.WizardButton.CancelButton, "Cancel")
    
    def accept(self):
        if self.finish_page.should_launch():
            # Launch the app
            try:
                if os.path.exists("main.py"):
                    subprocess.Popen([sys.executable, "main.py"])
                elif os.path.exists("XaykNoobsJournal.exe"):
                    subprocess.Popen(["XaykNoobsJournal.exe"])
            except:
                pass
        super().accept()


def run_cli_install():
    """Run installation in CLI mode"""
    print("=" * 60)
    print("XAYK NOOB'S JOURNAL - INSTALLER")
    print("=" * 60)
    print()
    print("This will install:")
    print("  1. Ollama (local AI runtime)")
    print("  2. LLaVA model (~4GB)")
    print("  3. App configuration")
    print()
    
    input("Press Enter to start installation...")
    print()
    
    worker = InstallWorker()
    success = worker._install()
    
    if success:
        print()
        print("=" * 60)
        print("INSTALLATION COMPLETE!")
        print("=" * 60)
        print()
        print("Run 'python main.py' to start the app.")
    else:
        print()
        print("Installation failed. Please check the errors above.")
    
    return 0 if success else 1


def main():
    if GUI_AVAILABLE:
        app = QApplication(sys.argv)
        wizard = InstallerWizard()
        wizard.show()
        return app.exec()
    else:
        return run_cli_install()


if __name__ == "__main__":
    sys.exit(main())
