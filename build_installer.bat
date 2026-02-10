@echo off
chcp 65001 >nul
title Build Installer - Xayk Noob's Journal

echo.
echo ============================================================
echo    XAYK NOOB'S JOURNAL - BUILD INSTALLER
echo ============================================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    pause
    exit /b 1
)

:: Check if venv exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else if exist "venv_win\Scripts\activate.bat" (
    call venv_win\Scripts\activate.bat
)

:: Install PyInstaller if needed
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

echo.
echo [1/2] Building main application...
echo.

pyinstaller --name=XaykNoobsJournal ^
    --onefile ^
    --windowed ^
    --add-data "guides;guides" ^
    --add-data "env.example;." ^
    --hidden-import=PIL ^
    --hidden-import=PIL.Image ^
    --hidden-import=cv2 ^
    --hidden-import=numpy ^
    --exclude-module=chromadb ^
    --exclude-module=langchain ^
    --exclude-module=langchain_community ^
    --exclude-module=langchain_core ^
    --exclude-module=langchain_text_splitters ^
    --exclude-module=sentence_transformers ^
    --exclude-module=torch ^
    --exclude-module=onnxruntime ^
    --exclude-module=fastembed ^
    --exclude-module=transformers ^
    --hidden-import=google.genai ^
    --hidden-import=PyQt6.QtWidgets ^
    --hidden-import=PyQt6.QtCore ^
    --hidden-import=PyQt6.QtGui ^
    --hidden-import=mss ^
    --hidden-import=win32gui ^
    --hidden-import=ollama ^
    --hidden-import=sklearn ^
    --hidden-import=sklearn.feature_extraction ^
    --hidden-import=sklearn.feature_extraction.text ^
    --hidden-import=sklearn.metrics ^
    --hidden-import=sklearn.metrics.pairwise ^
    --hidden-import=sklearn.utils._cython_blas ^
    --hidden-import=sklearn.neighbors._typedefs ^
    --hidden-import=sklearn.neighbors._quad_tree ^
    --hidden-import=sklearn.tree._utils ^
    --exclude-module=matplotlib ^
    --exclude-module=tkinter ^
    main.py

echo.
echo [2/2] Building installer...
echo.

pyinstaller --name=XaykNoobsJournal_Setup ^
    --onefile ^
    --windowed ^
    --hidden-import=PyQt6.QtWidgets ^
    --hidden-import=PyQt6.QtCore ^
    --hidden-import=PyQt6.QtGui ^
    installer.py

echo.
echo ============================================================
echo    BUILD COMPLETE!
echo ============================================================
echo.
echo Output files:
echo    dist\XaykNoobsJournal.exe      - Main application
echo    dist\XaykNoobsJournal_Setup.exe - Installer
echo.
echo To distribute:
echo    1. Share XaykNoobsJournal_Setup.exe
echo    2. Users run the setup, it installs everything
echo    3. Then they can run XaykNoobsJournal.exe
echo.
pause
