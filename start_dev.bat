@echo off
echo ==================================================
echo  Starting SkillBridge AI Platform (Fullstack)
echo ==================================================

echo Starting FastAPI Backend on http://localhost:8000 ...
start "SkillBridge Backend" /D "D:\Xcoder\Job-Portal\backend" python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

echo Starting Next.js Frontend on http://localhost:3000 ...
start "SkillBridge Frontend" /D "D:\Xcoder\Job-Portal\frontend" npm run dev

echo.
echo SkillBridge AI is live!
echo • Frontend UI: http://localhost:3000
echo • Backend API Docs: http://localhost:8000/docs
echo • Demo Student: student@ceg.edu / Student@123
echo • Demo TPO: tpo@ceg.edu / Tpo@123
echo.
pause

