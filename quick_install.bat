@echo off
chcp 65001 >nul
title Xayk Noob's Journal - Quick Install

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║     XAYK NOOB'S JOURNAL - QUICK INSTALL                   ║
echo ║     AI-Powered Retro Game Assistant                        ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
echo This will install:
echo   [1] Ollama - Local AI runtime
echo   [2] LLaVA  - Vision AI model (~4GB)
echo.
echo No internet required after installation.
echo No API keys or accounts needed.
echo.
echo ============================================================
pause

:: Check if Ollama is installed
echo.
echo [1/4] Checking Ollama installation...
ollama --version >nul 2>&1
if errorlevel 1 (
    echo       Ollama not found. Downloading...
    echo.
    
    :: Download Ollama
    echo       Downloading Ollama installer...
    curl -L -o "%TEMP%\OllamaSetup.exe" "https://ollama.com/download/OllamaSetup.exe"
    
    if not exist "%TEMP%\OllamaSetup.exe" (
        echo       ERROR: Failed to download Ollama!
        echo       Please download manually from: https://ollama.ai
        pause
        exit /b 1
    )
    
    echo       Installing Ollama (this may take a minute)...
    "%TEMP%\OllamaSetup.exe" /VERYSILENT /NORESTART
    
    :: Wait for installation
    timeout /t 10 /nobreak >nul
    
    :: Verify
    ollama --version >nul 2>&1
    if errorlevel 1 (
        echo       ERROR: Ollama installation failed!
        echo       Please install manually from: https://ollama.ai
        pause
        exit /b 1
    )
    echo       Ollama installed successfully!
) else (
    echo       Ollama already installed!
)

:: Start Ollama service
echo.
echo [2/4] Starting Ollama service...
start /b ollama serve >nul 2>&1
timeout /t 3 /nobreak >nul
echo       Service started!

:: Pull LLaVA model
echo.
echo [3/4] Downloading AI model (this will take a while)...
echo       Model size: ~4GB
echo       Please wait...
echo.
ollama pull llava

if errorlevel 1 (
    echo.
    echo       Trying smaller model...
    ollama pull llava:7b
)

:: Create config
echo.
echo [4/4] Creating configuration...
(
echo # Xayk Noob's Journal - Configuration
echo # Auto-configured by installer
echo.
echo LLM_PROVIDER=ollama
echo MODE=passive
) > .env
echo       Configuration created!

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║              INSTALLATION COMPLETE!                        ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
echo You can now run:
echo   - run.bat           (if using Python)
echo   - XaykNoobsJournal.exe (if using the built app)
echo.
echo How to use:
echo   1. Open your game in an emulator
echo   2. Run the app
echo   3. The overlay will show game guidance!
echo.
pause
