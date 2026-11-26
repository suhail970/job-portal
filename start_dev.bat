@echo off
setlocal EnableExtensions
chcp 65001 >nul
title SkillBridge AI Launcher

set "ROOT_DIR=%~dp0"
set "BACKEND_DIR=%ROOT_DIR%backend"
set "FRONTEND_DIR=%ROOT_DIR%frontend"

echo ==================================================
echo  Starting SkillBridge AI Platform (Fullstack)
echo ==================================================

if not exist "%BACKEND_DIR%\app\main.py" (
  echo [ERROR] Backend directory not found at "%BACKEND_DIR%"
  pause
  exit /b 1
)
if not exist "%FRONTEND_DIR%\package.json" (
  echo [ERROR] Frontend directory not found at "%FRONTEND_DIR%"
  pause
  exit /b 1
)

echo Checking ports 8000 and 3000...
for %%P in (8000 3000) do (
  for /f "tokens=5" %%A in ('netstat -ano ^| findstr /C:":%%P " ^| findstr "LISTENING"') do (
    if not "%%A"=="0" (
      echo Freeing busy port %%P [PID %%A]...
      taskkill /PID %%A /T /F >nul 2>&1
    )
  )
)

echo Starting FastAPI Backend on http://127.0.0.1:8000 ...
start "SkillBridge Backend" /D "%BACKEND_DIR%" cmd /k "python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

echo Starting Next.js Frontend on http://localhost:3000 ...
start "SkillBridge Frontend" /D "%FRONTEND_DIR%" cmd /k "npm run dev"

echo.
echo SkillBridge AI is starting in two console windows!
echo - Frontend UI:       http://localhost:3000
echo - Student Portal:    http://localhost:3000/student
echo - Backend API Docs:  http://127.0.0.1:8000/docs
echo - Demo Student:      student@ceg.edu / Student@123
echo - Demo TPO:          tpo@ceg.edu / Tpo@123
echo.
echo Keep the two server windows open while using the app.
echo Press any key in THIS launcher window to STOP both servers...
pause >nul

echo.
echo Stopping SkillBridge servers...
for %%P in (8000 3000) do (
  for /f "tokens=5" %%A in ('netstat -ano ^| findstr /C:":%%P " ^| findstr "LISTENING"') do (
    if not "%%A"=="0" (
      taskkill /PID %%A /T /F >nul 2>&1
    )
  )
)
taskkill /FI "WINDOWTITLE eq SkillBridge Backend*" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq SkillBridge Frontend*" /T /F >nul 2>&1
echo Servers stopped cleanly.
endlocal
