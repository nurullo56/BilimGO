@echo off
title BilimGo - All Services Runner
echo ======================================================
echo   BilimGo Tizimini ishga tushirish (Local + Cloudflare)
echo   Domen: https://bilimgo.smart-tools.uk
echo ======================================================

echo [1/3] Cloudflare Tunnel ishga tushirilmoqda...
start "BilimGo Tunnel" cmd /k "cd /d %~dp0 && cloudflared tunnel --config cloudflared_bilimgo.yml run"

timeout /t 2 /nobreak >nul

echo [2/3] FastAPI Web Server ishga tushirilmoqda (Port 8000)...
start "BilimGo FastAPI Web" cmd /k "cd /d %~dp0 && python -m uvicorn web.main:app --host 0.0.0.0 --port 8000 --reload"

timeout /t 2 /nobreak >nul

echo [3/4] Telegram Bot ishga tushirilmoqda...
start "BilimGo Bot" cmd /k "cd /d %~dp0 && python -m bot.main"

timeout /t 2 /nobreak >nul

echo [4/4] BilimGo UserBot va Video Relay Server ishga tushirilmoqda (Port 8081)...
start "BilimGo UserBot & Relay" cmd /k "cd /d C:\Users\Acer\Downloads\BilimGoUserBot\BilimGoUserBot && python main.py"

echo.
echo Barcha 4 ta xizmat alohida oynalarda ishga tushirildi!
echo Mini App manzili: https://bilimgo.smart-tools.uk
echo Lokal WebApp: http://localhost:8000
echo.
pause
