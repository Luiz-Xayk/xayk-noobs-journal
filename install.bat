@echo off
chcp 65001 >nul
title Xayk Noob's Journal - Installer

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║         XAYK NOOB'S JOURNAL - INSTALLER                   ║
echo ║         Your AI-powered retro game assistant!              ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

:: Check if Python is installed
echo [1/5] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: Python not found!
    echo Please install Python 3.10+ from: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation!
    echo.
    pause
    exit /b 1
)
echo       Python found!

:: Create virtual environment
echo.
echo [2/5] Creating virtual environment...
if exist "venv" (
    echo       Virtual environment already exists, skipping...
) else (
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment!
        pause
        exit /b 1
    )
    echo       Virtual environment created!
)

:: Activate virtual environment
echo.
echo [3/5] Activating virtual environment...
call venv\Scripts\activate.bat

:: Install dependencies
echo.
echo [4/5] Installing dependencies (this may take a few minutes)...
echo       Downloading AI models and libraries...
pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies!
    pause
    exit /b 1
)
echo       Dependencies installed!

:: Create .env file
echo.
echo [5/5] Setting up configuration...
if not exist ".env" (
    copy env.example .env >nul 2>&1
    if not exist ".env" (
        echo GEMINI_API_KEY=your_gemini_api_key_here> .env
    )
    echo       Created .env file!
    echo.
    echo ╔════════════════════════════════════════════════════════════╗
    echo ║  IMPORTANT: You need to add your Gemini API key!           ║
    echo ║                                                            ║
    echo ║  1. Open the .env file in this folder                      ║
    echo ║  2. Get a free API key from:                               ║
    echo ║     https://aistudio.google.com/app/apikey                 ║
    echo ║  3. Replace 'your_gemini_api_key_here' with your key       ║
    echo ╚════════════════════════════════════════════════════════════╝
) else (
    echo       Configuration file already exists!
)

:: Index knowledge base
echo.
echo [BONUS] Indexing game guides...
python main.py --mode reindex

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║              INSTALLATION COMPLETE!                        ║
echo ║                                                            ║
echo ║  To start: Double-click 'run.bat'                          ║
echo ║                                                            ║
echo ║  Don't forget to configure your API key in .env file!      ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
pause
