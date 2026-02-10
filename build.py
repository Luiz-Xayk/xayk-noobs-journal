"""
Build script for Xayk Noob's Journal
Creates a standalone .exe that works without Python installed
"""

import subprocess
import sys
import shutil
from pathlib import Path


def build():
    print("=" * 60)
    print("XAYK NOOB'S JOURNAL - BUILD SCRIPT")
    print("=" * 60)
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
        print(f"PyInstaller version: {PyInstaller.__version__}")
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # Clean previous builds
    print("\n[1/4] Cleaning previous builds...")
    for folder in ["build", "dist"]:
        if Path(folder).exists():
            shutil.rmtree(folder)
    
    for spec in Path(".").glob("*.spec"):
        spec.unlink()
    
    # Prepare data files
    print("\n[2/4] Preparing data files...")
    
    # PyInstaller command
    print("\n[3/4] Building executable...")
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=XaykNoobsJournal",
        "--onefile",
        "--windowed",
        "--icon=NONE",
        # Add data files
        "--add-data=guides;guides",
        "--add-data=env.example;.",
        # Hidden imports for dependencies
        "--hidden-import=PIL",
        "--hidden-import=PIL.Image",
        "--hidden-import=cv2",
        "--hidden-import=numpy",
        # Exclude heavy ML modules (not needed anymore)
        "--exclude-module=chromadb",
        "--exclude-module=langchain",
        "--exclude-module=langchain_community",
        "--exclude-module=langchain_core",
        "--exclude-module=langchain_text_splitters",
        "--exclude-module=sentence_transformers",
        "--exclude-module=torch",
        "--exclude-module=onnxruntime",
        "--exclude-module=fastembed",
        "--exclude-module=transformers",
        "--hidden-import=google.genai",
        "--hidden-import=ollama",
        "--hidden-import=google.generativeai",
        "--hidden-import=PyQt6",
        "--hidden-import=PyQt6.QtWidgets",
        "--hidden-import=PyQt6.QtCore",
        "--hidden-import=PyQt6.QtGui",
        "--hidden-import=mss",
        "--hidden-import=win32gui",
        "--hidden-import=win32con",
        "--hidden-import=sklearn",
        "--hidden-import=sklearn.feature_extraction",
        "--hidden-import=sklearn.feature_extraction.text",
        "--hidden-import=sklearn.metrics",
        "--hidden-import=sklearn.metrics.pairwise",
        "--hidden-import=sklearn.utils._cython_blas",
        "--hidden-import=sklearn.neighbors._typedefs",
        "--hidden-import=sklearn.neighbors._quad_tree",
        "--hidden-import=sklearn.tree._utils",
        # Exclude unnecessary modules to reduce size
        "--exclude-module=matplotlib",
        "--exclude-module=tkinter",
        "--exclude-module=scipy",
        # Main script
        "main.py"
    ]
    
    result = subprocess.run(cmd)
    
    if result.returncode != 0:
        print("\nBuild failed!")
        return 1
    
    # Post-build: copy necessary files
    print("\n[4/4] Finalizing...")
    
    dist_path = Path("dist")
    
    # Copy guides folder
    if Path("guides").exists():
        shutil.copytree("guides", dist_path / "guides", dirs_exist_ok=True)
    
    # Copy env.example
    if Path("env.example").exists():
        shutil.copy("env.example", dist_path / "env.example")
    
    # Create README for distribution
    readme_content = """XAYK NOOB'S JOURNAL
===================

Quick Start:
1. Run XaykNoobsJournal.exe
2. On first run, you'll be asked for a Gemini API key
3. Get your free key at: https://aistudio.google.com/app/apikey
4. Open your game in an emulator
5. The overlay will appear with guidance!

Adding Game Guides:
- Add .txt files to the guides/ folder
- Organize by game: guides/GameName/game_data.txt

For more info: https://github.com/Luiz-Xayk/xayk-noobs-journal
"""
    
    (dist_path / "README.txt").write_text(readme_content)
    
    print("\n" + "=" * 60)
    print("BUILD COMPLETE!")
    print("=" * 60)
    print(f"\nOutput: {dist_path / 'XaykNoobsJournal.exe'}")
    print("\nTo distribute, share the entire 'dist' folder.")
    
    return 0


if __name__ == "__main__":
    sys.exit(build())
