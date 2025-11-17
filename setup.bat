@echo off
REM Fandango Scraper Setup Script for Windows

echo ==========================================
echo Fandango Scraper Setup
echo ==========================================
echo.

REM Step 1: Check for Python
echo Step 1: Checking for Python installation...
python --version >nul 2>&1
if %errorlevel% == 0 (
    echo [OK] Python found
    python --version
) else (
    py --version >nul 2>&1
    if %errorlevel% == 0 (
        echo [OK] Python found
        py --version
    ) else (
        echo [ERROR] Python not found!
        echo.
        echo Please install Python 3.8+ from:
        echo   https://www.python.org/downloads/
        echo.
        echo Make sure to check "Add Python to PATH" during installation!
        pause
        exit /b 1
    )
)

echo.

REM Step 2: Create virtual environment
echo Step 2: Creating virtual environment...
if exist venv (
    echo [SKIP] Virtual environment already exists
) else (
    python -m venv venv
    if %errorlevel% == 0 (
        echo [OK] Virtual environment created
    ) else (
        py -m venv venv
        echo [OK] Virtual environment created
    )
)

echo.
echo ==========================================
echo Setup Complete!
echo ==========================================
echo.
echo Next steps:
echo.
echo 1. Activate the virtual environment:
echo    venv\Scripts\activate
echo.
echo 2. Install dependencies:
echo    pip install -r requirements.txt
echo.
echo 3. Test Firebase connection:
echo    python test_firebase.py
echo.
echo 4. Run the scraper:
echo    python main.py --dry-run --no-headless
echo.
pause
