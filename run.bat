@echo off
chcp 65001 >nul
title Xayk Noob's Journal

:: Check if venv exists
if not exist "venv\Scripts\activate.bat" (
    echo Virtual environment not found!
    echo Please run install.bat first.
    pause
    exit /b 1
)

:: Activate and run
call venv\Scripts\activate.bat
python main.py %*
