# SkillBridge AI — One-Click Development Launch Script

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host " Starting SkillBridge AI Platform (Fullstack)" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# 1. Start FastAPI Backend on Port 8000
Write-Host "Starting FastAPI Backend on http://localhost:8000 ..." -ForegroundColor Green
$backendProcess = Start-Process -FilePath "python" -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000", "--reload" -WorkingDirectory "D:\Xcoder\Job-Portal\backend" -PassThru

# 2. Start Next.js Frontend on Port 3000
Write-Host "Starting Next.js Frontend on http://localhost:3000 ..." -ForegroundColor Green
$frontendProcess = Start-Process -FilePath "npm" -ArgumentList "run", "dev" -WorkingDirectory "D:\Xcoder\Job-Portal\frontend" -PassThru

Write-Host ""
Write-Host "SkillBridge AI is live!" -ForegroundColor Green
Write-Host "• Frontend UI: http://localhost:3000" -ForegroundColor White
Write-Host "• Backend API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "• Demo Student: student@ceg.edu / Student@123" -ForegroundColor Yellow
Write-Host "• Demo TPO: tpo@ceg.edu / Tpo@123" -ForegroundColor Yellow
Write-Host "• Demo Admin: admin@skillbridge.ai / Admin@123" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press Enter to stop both servers..." -ForegroundColor Cyan
Read-Host

Stop-Process -Id $backendProcess.Id -Force
Stop-Process -Id $frontendProcess.Id -Force
Write-Host "Servers stopped." -ForegroundColor Red

