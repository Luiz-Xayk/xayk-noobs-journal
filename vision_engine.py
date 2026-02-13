import cv2
import numpy as np
import mss
from PIL import Image
from pathlib import Path
from typing import Optional, Tuple, List, Dict
import json
import time

try:
    import win32gui
    import win32con
    WINDOWS_AVAILABLE = True
except ImportError:
    WINDOWS_AVAILABLE = False


class VisionEngine:
    
    EMULATOR_TITLES = [
        "DuckStation",
        "PCSX2",
        "ePSXe",
        "RetroArch",
        "Beetle PSX",
        "PPSSPP",
        "Dolphin",
        "Cemu",
        "mGBA",
        "VisualBoyAdvance",
        "Citra",
        "Yuzu",
        "Ryujinx",
        "RPCS3",
        "Xenia",
    ]
    
    # Known game titles to detect emulator windows by game name
    GAME_KEYWORDS = [
        "Metal Gear Solid",
        "Resident Evil",
        "Silent Hill",
        "Final Fantasy",
        "Castlevania",
        "Mega Man",
        "Crash Bandicoot",
        "Spyro",
        "Tomb Raider",
        "God of War",
        "Kingdom Hearts",
        "Devil May Cry",
        "Tekken",
        "Gran Turismo",
        "Sons of Liberty",
        "Snake Eater",
        "Twin Snakes",
        "Dino Crisis",
    ]
    
    def __init__(self, debug_folder: str = "debug"):
        self.debug_folder = Path(debug_folder)
        self.debug_folder.mkdir(exist_ok=True)
        
        print("Vision engine initialized")
        
        self.target_window_handle: Optional[int] = None
        self.target_window_title: str = ""
        
        self.roi_config: Optional[Dict] = None
        self.load_roi_config()
        
    def load_roi_config(self):
        roi_file = Path("roi_config.json")
        if roi_file.exists():
            with open(roi_file, 'r') as f:
                self.roi_config = json.load(f)
    
    def save_roi_config(self, x_percent: float, y_percent: float, 
                        width_percent: float, height_percent: float):
        self.roi_config = {
            "x": x_percent,
            "y": y_percent,
            "width": width_percent,
            "height": height_percent
        }
        with open("roi_config.json", 'w') as f:
            json.dump(self.roi_config, f, indent=2)
    
    def set_default_ps1_roi(self):
        self.save_roi_config(
            x_percent=0.10,
            y_percent=0.70,
            width_percent=0.80,
            height_percent=0.25
        )
    
    # Window titles to EXCLUDE (browsers, IDEs, etc.)
    EXCLUDED_WINDOWS = [
        "chrome", "firefox", "edge", "opera", "brave", "safari", "vivaldi",
        "cursor", "vscode", "visual studio", "code -", "notepad", "sublime",
        "discord", "slack", "telegram", "whatsapp", "spotify",
        "explorer", "task manager", "powershell", "cmd.exe", "terminal",
        "gamefaqs", "youtube", "twitch", "reddit", "google",
    ]
    
    def _is_excluded_window(self, title: str) -> bool:
        """Check if window title belongs to a browser, IDE, or other non-game app"""
        title_lower = title.lower()
        for excluded in self.EXCLUDED_WINDOWS:
            if excluded in title_lower:
                return True
        return False
    
    def find_emulator_window(self, custom_title: Optional[str] = None) -> bool:
        if not WINDOWS_AVAILABLE:
            return False
        
        # Collect ALL visible windows first
        all_windows = []
        
        def enum_callback(hwnd, windows_list):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title and len(title) > 2:
                    windows_list.append((hwnd, title))
            return True
        
        win32gui.EnumWindows(enum_callback, all_windows)
        
        # Custom title: search directly but still exclude browsers
        if custom_title:
            for hwnd, title in all_windows:
                if custom_title.lower() in title.lower() and not self._is_excluded_window(title):
                    self.target_window_handle = hwnd
                    self.target_window_title = title
                    print(f"Window found: '{title}'")
                    return True
        
        # PHASE 1: Search for known emulator names (highest priority)
        for hwnd, title in all_windows:
            title_lower = title.lower()
            for emu_name in self.EMULATOR_TITLES:
                if emu_name.lower() in title_lower:
                    self.target_window_handle = hwnd
                    self.target_window_title = title
                    print(f"Emulator found: '{title}'")
                    return True
        
        # PHASE 2: Search by game keywords but EXCLUDE browsers/IDEs/etc
        for hwnd, title in all_windows:
            if self._is_excluded_window(title):
                continue
            title_lower = title.lower()
            for game_keyword in self.GAME_KEYWORDS:
                if game_keyword.lower() in title_lower:
                    self.target_window_handle = hwnd
                    self.target_window_title = title
                    print(f"Game window found: '{title}'")
                    return True
        
        # PHASE 3: Last resort - print available windows for debugging
        print("No emulator window found. Visible windows:")
        for hwnd, title in all_windows[:15]:
            excluded = " [EXCLUDED]" if self._is_excluded_window(title) else ""
            print(f"  - '{title}'{excluded}")
        
        return False
    
    def get_window_rect(self) -> Optional[Tuple[int, int, int, int]]:
        if not WINDOWS_AVAILABLE or not self.target_window_handle:
            return None
        
        try:
            rect = win32gui.GetWindowRect(self.target_window_handle)
            return rect
        except Exception:
            return None
    
    def capture_screen(self, save_debug: bool = False) -> Optional[np.ndarray]:
        rect = self.get_window_rect()
        
        if rect:
            left, top, right, bottom = rect
            monitor = {
                "left": left,
                "top": top,
                "width": right - left,
                "height": bottom - top
            }
        else:
            with mss.mss() as sct:
                monitor = sct.monitors[1]
        
        with mss.mss() as sct:
            screenshot = sct.grab(monitor)
            frame = np.array(screenshot)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
        
        if save_debug:
            timestamp = int(time.time())
            debug_path = self.debug_folder / f"capture_{timestamp}.png"
            cv2.imwrite(str(debug_path), frame)
        
        return frame
    
    def apply_roi(self, frame: np.ndarray) -> np.ndarray:
        if not self.roi_config:
            return frame
        
        height, width = frame.shape[:2]
        
        x = int(width * self.roi_config["x"])
        y = int(height * self.roi_config["y"])
        w = int(width * self.roi_config["width"])
        h = int(height * self.roi_config["height"])
        
        x = max(0, min(x, width - 1))
        y = max(0, min(y, height - 1))
        w = max(1, min(w, width - x))
        h = max(1, min(h, height - y))
        
        return frame[y:y+h, x:x+w]
    
    def preprocess_frame(self, frame: np.ndarray, save_debug: bool = False) -> np.ndarray:
        roi_frame = self.apply_roi(frame)
        gray = cv2.cvtColor(roi_frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.convertScaleAbs(gray, alpha=1.5, beta=0)
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        
        processed = cv2.adaptiveThreshold(
            blurred, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11, 2
        )
        
        if save_debug:
            timestamp = int(time.time())
            cv2.imwrite(str(self.debug_folder / f"roi_{timestamp}.png"), roi_frame)
            cv2.imwrite(str(self.debug_folder / f"processed_{timestamp}.png"), processed)
        
        return processed
    
    def get_frame_for_analysis(self, save_debug: bool = False) -> Optional[np.ndarray]:
        """Get a frame ready for AI vision analysis"""
        frame = self.capture_screen(save_debug=save_debug)
        if frame is None:
            return None
        return frame
    
    def draw_debug_overlay(self, frame: np.ndarray, results: List[Dict]) -> np.ndarray:
        debug_frame = frame.copy()
        
        for result in results:
            bbox = result.get("bbox", [])
            text = result["text"]
            conf = result["confidence"]
            
            pts = np.array(bbox, dtype=np.int32)
            cv2.polylines(debug_frame, [pts], True, (0, 255, 0), 2)
            
            x, y = int(bbox[0][0]), int(bbox[0][1]) - 10
            cv2.putText(debug_frame, f"{text} ({conf:.2f})", 
                       (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        return debug_frame


def main():
    print("=" * 50)
    print("Xayk Noob's Journal - Vision Engine Test")
    print("=" * 50)
    
    engine = VisionEngine()
    
    print("\nSearching for emulator window...")
    found = engine.find_emulator_window()
    
    if not found:
        print("\nTip: Open DuckStation or PCSX2 and run again.")
    
    if not engine.roi_config:
        print("\nSetting default PS1 ROI...")
        engine.set_default_ps1_roi()
    
    print("\nCapturing frame...")
    frame = engine.get_frame_for_analysis(save_debug=True)
    
    if frame is not None:
        print(f"Frame captured: {frame.shape}")
        print("Frame ready for AI analysis")
    else:
        print("Failed to capture frame")
    
    print(f"\nDebug frames saved to: {engine.debug_folder.absolute()}")


if __name__ == "__main__":
    main()
