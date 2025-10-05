@echo off

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH. Please install Python first.
    pause
    exit /b 1
)

REM Check if Flask is installed
pip show Flask >nul 2>&1
if %errorlevel% neq 0 (
    echo Flask is not installed. Installing Flask...
    pip install Flask
    if %errorlevel% neq 0 (
        echo Failed to install Flask. Please check your internet connection or Python/pip installation.
        pause
        exit /b 1
    )
    echo Flask installed successfully.
)

REM Run the Flask application
python app.py
pausepython app.py