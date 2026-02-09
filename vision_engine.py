import cv2
import numpy as np
import mss
import easyocr
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
    ]
    
    def __init__(self, debug_folder: str = "debug"):
        self.debug_folder = Path(debug_folder)
        self.debug_folder.mkdir(exist_ok=True)
        
        print("Loading OCR models...")
        self.reader = easyocr.Reader(['en'], gpu=False)
        print("OCR loaded!")
        
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
    
    def find_emulator_window(self, custom_title: Optional[str] = None) -> bool:
        if not WINDOWS_AVAILABLE:
            return False
        
        titles_to_search = [custom_title] if custom_title else self.EMULATOR_TITLES
        
        def callback(hwnd, results):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                for search_title in titles_to_search:
                    if search_title and search_title.lower() in title.lower():
                        results.append((hwnd, title))
            return True
        
        results = []
        win32gui.EnumWindows(callback, results)
        
        if results:
            self.target_window_handle, self.target_window_title = results[0]
            print(f"Window found: '{self.target_window_title}'")
            return True
        
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
    
    def extract_text(self, frame: np.ndarray, min_confidence: float = 0.3,
                     min_length: int = 2) -> List[Dict]:
        results = self.reader.readtext(frame)
        
        extracted = []
        for (bbox, text, confidence) in results:
            if confidence >= min_confidence and len(text.strip()) >= min_length:
                extracted.append({
                    "text": text.strip(),
                    "confidence": confidence,
                    "bbox": bbox
                })
        
        return extracted
    
    def get_screen_text(self, save_debug: bool = False) -> str:
        frame = self.capture_screen(save_debug=save_debug)
        if frame is None:
            return ""
        
        processed = self.preprocess_frame(frame, save_debug=save_debug)
        results = self.extract_text(processed)
        texts = [r["text"] for r in results]
        
        return " ".join(texts)
    
    def draw_debug_overlay(self, frame: np.ndarray, results: List[Dict]) -> np.ndarray:
        debug_frame = frame.copy()
        
        for result in results:
            bbox = result["bbox"]
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
    
    print("\nCapturing and processing frame...")
    text = engine.get_screen_text(save_debug=True)
    
    if text:
        print(f"\nText detected:\n{'-' * 40}\n{text}\n{'-' * 40}")
    else:
        print("\nNo text detected.")
    
    print(f"\nDebug frames saved to: {engine.debug_folder.absolute()}")


if __name__ == "__main__":
    main()
