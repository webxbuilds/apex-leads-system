@echo off
echo ===================================================
echo   Apex Website Agency Operating System Launcher
echo ===================================================
echo.

:: Check for .env file in root
if not exist .env (
    echo [INFO] Creating .env file from .env.example...
    copy .env.example .env
)

:: Start Backend FastAPI Server
echo [1/2] Launching Backend Server on port 8000...
start "Apex Backend (FastAPI)" cmd /k "cd /d %~dp0 && echo Starting Backend... && .\backend\venv\Scripts\python -m uvicorn backend.app.main:app --reload --port 8000"

:: Start Frontend React Server
echo [2/2] Launching Frontend React Server...
start "Apex Frontend (React)" cmd /k "cd /d %~dp0\frontend && echo Starting Frontend... && npm run dev"

echo.
echo ===================================================
echo   System launched successfully!
echo   - Backend API Docs: http://127.0.0.1:8000/docs
echo   - Frontend Portal:  http://localhost:5173
echo ===================================================
pause
