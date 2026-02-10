@echo off
chcp 65001 >nul
title Rebuild EXE - Xayk Noob's Journal

echo.
echo ============================================================
echo    REBUILDING XAYK NOOB'S JOURNAL .EXE FILES
echo ============================================================
echo.

:: Activate venv
call venv_win\Scripts\activate.bat

:: Clean old builds
echo [1/3] Cleaning old builds...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "*.spec" del /q "*.spec"

:: Build main app
echo.
echo [2/3] Building main application...
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

:: Build installer
echo.
echo [3/3] Building installer...
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
echo You can now test XaykNoobsJournal_Setup.exe
echo.
pause
