@echo off
echo ============================================
echo  BioEthics Radar — Semantic Analysis Engine
echo ============================================
echo.

:: Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

:: Install dependencies if needed
echo [1/3] Checking dependencies...
pip install -r requirements.txt --quiet

echo [2/3] Pre-loading sentence-transformer model (first run may take ~30s)...
echo [3/3] Starting FastAPI server on http://localhost:8000
echo.
echo  >> API Docs:    http://localhost:8000/docs
echo  >> Health:      http://localhost:8000/health
echo  >> Frontend:    Open index.html in parent folder
echo.
echo Press Ctrl+C to stop the server.
echo.

cd /d "%~dp0"
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

pause
