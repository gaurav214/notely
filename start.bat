@echo off
REM Blackboard Notes Generator - Quick Start Script for Windows

echo.
echo ========================================
echo Blackboard Notes Generator - Startup
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo Error: Failed to create virtual environment
        echo Make sure Python 3.8+ is installed and in PATH
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install requirements if needed
echo Checking dependencies...
pip list | findstr /i "fastapi streamlit pytesseract" >nul
if %errorlevel% neq 0 (
    echo Installing dependencies...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo Error: Failed to install dependencies
        pause
        exit /b 1
    )
)

REM Check if .env file exists
if not exist ".env" (
    echo.
    echo ⚠️  WARNING: .env file not found!
    echo Please create .env file with your GROQ_API_KEY
    echo Copy .env.example to .env and fill in your API key
    echo.
    echo Get free Groq API key from: https://console.groq.com/keys
    echo.
    pause
    exit /b 1
)

REM Check Tesseract installation
echo Checking Tesseract OCR...
where tesseract >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ⚠️  WARNING: Tesseract OCR not found in PATH!
    echo Please install Tesseract OCR from:
    echo https://github.com/UB-Mannheim/tesseract/wiki
    echo.
    echo Or set TESSERACT_PATH in your .env file
    echo.
    pause
    exit /b 1
)

echo.
echo ✅ All checks passed!
echo.
echo Starting Blackboard Notes Generator...
echo.

REM Create two terminal windows for backend and frontend
echo Opening FastAPI Backend...
start "Blackboard Notes - Backend" cmd /k "cd /d %cd% && venv\Scripts\activate.bat && python main.py"

timeout /t 3 /nobreak

echo Opening Streamlit Frontend...
start "Blackboard Notes - Frontend" cmd /k "cd /d %cd% && venv\Scripts\activate.bat && streamlit run frontend.py"

echo.
echo ========================================
echo ✅ Application starting...
echo ========================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:8501
echo.
echo Closing this window will not stop the servers.
echo To stop, close the other terminal windows.
echo.
pause
