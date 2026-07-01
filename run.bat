@echo off
title Personal Finance Manager
echo ========================================================
echo   Starting Personal Finance Manager...
echo ========================================================
echo.

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in your PATH environment variable!
    echo Please install Python: https://www.python.org/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b
)

echo [INFO] Verifying libraries...
python -c "import PyQt5, matplotlib, yfinance" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Required libraries not found. Installing dependencies...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [ERROR] Dependency installation failed. Please check your internet connection.
        echo.
        pause
        exit /b
    )
)

echo [INFO] Launching application...
start pythonw personal_finance.py
exit /b
